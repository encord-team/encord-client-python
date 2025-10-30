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
    """Settings for uploading data into GCP cloud storage.

    These apply for each individual upload and will overwrite
    the :meth:`encord.http.constants.RequestsSettings` defined during
    :class:`encord.EncordUserClient` creation.
    """

    max_retries: Optional[int] = None
    """Maximum number of allowed retries when uploading a file."""

    backoff_factor: Optional[float] = None
    """Factor used to calculate exponential backoff between retries.

    The delay before each retry is computed as:
    ``backoff_factor * (2 ** (retry_number - 1))``.
    """

    allow_failures: bool = False
    """Whether to allow partial failures during upload.

    If set to True, the upload will proceed even if some items fail
    after all retries. Failed uploads will be logged, and the process
    will continue. This is useful for large batch uploads where a few
    failures are acceptable.
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
    """Split an iterable into fixed-size batches.

    Args:
        iterable (List): The input list to be split.
        n (int): The maximum size of each batch.

    Returns:
        List[List]: A list of lists where each sublist represents a batch.

    Note:
        This can be replaced with :func:`itertools.batched` in Python 3.12+.
    """
    return [iterable[ndx : min(ndx + n, len(iterable))] for ndx in range(0, len(iterable), n)]


@dataclass
class UploadToSignedUrlFailure:
    """Details of a failed upload attempt to a signed URL."""

    exception: Exception
    """The exception instance raised during the failed upload."""

    file_path: Union[str, Path]
    """Path to the file that failed to upload."""

    title: str
    """Title or identifier associated with the file."""

    signed_url: str
    """The signed URL that the file upload was attempted against."""


def upload_to_signed_url_list_for_single_file(
    failures: List[UploadToSignedUrlFailure],
    file_path: Union[str, Path],
    title: str,
    signed_url: str,
    upload_item_type: StorageItemType,
    max_retries: int,
    backoff_factor: float,
) -> None:
    """Attempt to upload a single file to a signed URL, appending failures if any occur.

    Args:
        failures (List[UploadToSignedUrlFailure]): A list to append failures to.
        file_path (Union[str, Path]): Path of the file to upload.
        title (str): Title or identifier for the file.
        signed_url (str): The signed URL to upload the file to.
        upload_item_type (StorageItemType): The type of the file being uploaded.
        max_retries (int): Maximum number of retries in case of failure.
        backoff_factor (float): Backoff factor for retry delays.
    """
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
    """Parameters for requesting presigned URLs for file uploads."""

    count: int
    """Number of presigned URLs to request, typically matching the batch size of files."""

    upload_item_type: StorageItemType
    """The type of item being uploaded (e.g., IMAGE, VIDEO, AUDIO, DICOM)."""


def upload_to_signed_url_list(
    file_paths: Iterable[Union[str, Path]],
    config: BaseConfig,
    api_client: ApiClient,
    upload_item_type: StorageItemType,
    cloud_upload_settings: CloudUploadSettings,
) -> List[Dict]:
    """Upload multiple files to signed URLs and return upload results.

    Args:
        file_paths (Iterable[Union[str, Path]]): Paths of files to upload.
        config (BaseConfig): Configuration object with request settings.
        api_client (ApiClient): API client used to fetch presigned URLs.
        upload_item_type (StorageItemType): Type of items being uploaded.
        cloud_upload_settings (CloudUploadSettings): Upload configuration.

    Returns:
        List[Dict]: A list of dictionaries containing upload metadata:
            - ``data_hash`` (str): Unique identifier for the file.
            - ``file_link`` (str): Link to the uploaded file in storage.
            - ``title`` (str): File name or title.

    Raises:
        EncordException: If any file path does not exist.
        CloudUploadError: If uploads fail and ``allow_failures`` is False.
    """
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
