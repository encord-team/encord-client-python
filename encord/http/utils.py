"""---
title: "CloudUpload"
slug: "sdk-ref-cloudupload"
hidden: false
metadata:
  title: "CloudUpload"
  description: "Encord SDK CloudUpload class."
category: "64e481b57b6027003f20aaa0"
---
"""

import logging
import mimetypes
import os.path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Type, Union

from tqdm import tqdm

from encord.configs import BaseConfig
from encord.exceptions import CloudUploadError, EncordException
from encord.http.querier import Querier, create_new_session
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.base_dto import BaseDTO
from encord.orm.dataset import (
    Audio,
    DicomSeries,
    Images,
    SignedImagesURL,
    Video,
)
from encord.orm.storage import StorageItemType, UploadSignedUrl

PROGRESS_BAR_FILE_FACTOR = 100
CACHE_DURATION_IN_SECONDS = 24 * 60 * 60  # 1 day
UPLOAD_TO_SIGNED_URL_LIST_MAX_WORKERS = 4
UPLOAD_TO_SIGNED_URL_LIST_SIGNED_URLS_BATCH_SIZE = 200

logger = logging.getLogger(__name__)


@dataclass
class CloudUploadSettings:
    """The settings for uploading data into the GCP cloud storage. These apply for each individual upload. These settings
    will overwrite the :meth:`encord.http.constants.RequestsSettings` which is set during
    :class:`encord.EncordUserClient` creation.
    """

    max_retries: Optional[int] = None
    """Number of allowed retries when uploading"""
    backoff_factor: Optional[float] = None
    """With each retry, there will be a sleep of backoff_factor * (2 ** (retry_number - 1) )"""
    allow_failures: bool = False
    """
    If failures are allowed, the upload will continue even if some items were not successfully uploaded even
    after retries. For example, upon creation of a large image group, you might want to create the image group
    even if a few images were not successfully uploaded. The unsuccessfully uploaded images will then be logged.
    """


def _get_content_type(
    upload_item_type: StorageItemType,
    file_path: Union[str, Path],
) -> Optional[str]:
    if upload_item_type == StorageItemType.IMAGE:
        return mimetypes.guess_type(str(file_path))[0]
    if upload_item_type == StorageItemType.VIDEO or upload_item_type == StorageItemType.AUDIO:
        return "application/octet-stream"
    elif upload_item_type == StorageItemType.DICOM_FILE:
        return "application/dicom"
    else:
        raise ValueError(f"Unsupported {upload_item_type=}")


def get_batches(iterable: List, n: int) -> List[List]:
    # could be replaced with itertools.batched in python3.12
    return [iterable[ndx : min(ndx + n, len(iterable))] for ndx in range(0, len(iterable), n)]


@dataclass
class UploadToSignedUrlFailure:
    exception: Exception
    file_path: Union[str, Path]
    title: str
    signed_url: str


def upload_to_signed_url_list_for_single_file(
    failures: List[UploadToSignedUrlFailure],
    file_path: Union[str, Path],
    title: str,
    signed_url: str,
    upload_item_type: StorageItemType,
    max_retries: int,
    backoff_factor: float,
) -> None:
    try:
        _upload_single_file(
            file_path,
            title,
            signed_url,
            _get_content_type(upload_item_type, file_path),
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )
    except CloudUploadError as e:
        failures.append(
            UploadToSignedUrlFailure(
                exception=e,
                file_path=file_path,
                title=title,
                signed_url=signed_url,
            )
        )


class UploadPresignedUrlsGetParams(BaseDTO):
    count: int
    upload_item_type: StorageItemType


def upload_to_signed_url_list(
    file_paths: Iterable[Union[str, Path]],
    config: BaseConfig,
    api_client: ApiClient,
    upload_item_type: StorageItemType,
    cloud_upload_settings: CloudUploadSettings,
) -> List[Dict]:
    """Upload files and return the upload returns in the same order as the file paths supplied."""
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise EncordException(message=f"{file_path} does not point to a file.")

    signed_urls = []

    for file_path_batch in get_batches(list(file_paths), n=UPLOAD_TO_SIGNED_URL_LIST_SIGNED_URLS_BATCH_SIZE):
        file_names_batch = [os.path.basename(str(x)) for x in file_path_batch]

        signed_urls_batch = [
            {
                "data_hash": str(x.item_uuid),
                "file_link": x.object_key,
                "signed_url": x.signed_url,
            }
            for x in api_client.get(
                f"presigned-urls",
                params=UploadPresignedUrlsGetParams(
                    count=len(file_names_batch),
                    upload_item_type=upload_item_type,
                ),
                result_type=Page[UploadSignedUrl],
            ).results
        ]
        assert len(file_names_batch) == len(signed_urls_batch)

        for file_name, signed_url in zip(file_names_batch, signed_urls_batch):
            signed_url["title"] = file_name
            signed_urls.append(signed_url)

    failures: List[UploadToSignedUrlFailure] = []
    assert len(list(file_paths)) == len(signed_urls)

    with ThreadPoolExecutor(max_workers=UPLOAD_TO_SIGNED_URL_LIST_MAX_WORKERS) as executor:
        list(
            tqdm(
                executor.map(
                    lambda args: upload_to_signed_url_list_for_single_file(
                        failures,
                        args[0],
                        args[1]["title"],
                        args[1]["signed_url"],
                        upload_item_type,
                        max_retries=cloud_upload_settings.max_retries or config.requests_settings.max_retries,
                        backoff_factor=cloud_upload_settings.backoff_factor or config.requests_settings.backoff_factor,
                    ),
                    zip(file_paths, signed_urls),
                ),
                total=len(list(file_paths)),
            )
        )

    if failures:
        # TODO consider dropping support for allow_failures in the future
        # TODO allow_failures would only ignore networking issues
        # TODO we do check for files presence in this function (at the beginning)
        if cloud_upload_settings.allow_failures:
            logger.warning("The upload was incomplete for the following items: %s", [x.file_path for x in failures])
        else:
            raise failures[0].exception

    signed_urls_failed = [x.signed_url for x in failures]

    return [
        {
            "data_hash": x["data_hash"],
            "file_link": x["file_link"],
            "title": x["title"],
        }
        for x in signed_urls
        if x["signed_url"] not in signed_urls_failed
    ]


def _upload_single_file(
    file_path: Union[str, Path],
    title: str,
    signed_url: str,
    content_type: Optional[str],
    *,
    max_retries: int,
    backoff_factor: float,
    cache_max_age: int = CACHE_DURATION_IN_SECONDS,
) -> None:
    with create_new_session(
        max_retries=max_retries, backoff_factor=backoff_factor, connect_retries=max_retries
    ) as session:
        with open(file_path, "rb") as f:
            res_upload = session.put(
                signed_url, data=f, headers={"Content-Type": content_type, "Cache-Control": f"max-age={cache_max_age}"}
            )

            if res_upload.status_code != 200:
                status_code = res_upload.status_code
                headers = res_upload.headers
                res_text = res_upload.text
                error_string = str(
                    f"Error uploading file '{title}' to signed url: "
                    f"'{signed_url}'.\n"
                    f"Response data:\n\tstatus code: '{status_code}'\n\theaders: '{headers}'\n\tcontent: '{res_text}'",
                )

                logger.error(error_string)
                raise CloudUploadError(error_string)
