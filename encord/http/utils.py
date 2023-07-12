import logging
import mimetypes
import os.path
from dataclasses import dataclass
from typing import Iterable, List, Optional, Type, TypeVar, Union

from tqdm import tqdm

from encord.configs import BaseConfig
from encord.exceptions import CloudUploadError
from encord.http.querier import Querier, create_new_session
from encord.orm.dataset import (
    DicomSeries,
    Images,
    SignedDicomsURL,
    SignedDicomURL,
    SignedImagesURL,
    SignedImageURL,
    SignedVideoURL,
    Video,
)

PROGRESS_BAR_FILE_FACTOR = 100
CACHE_DURATION_IN_SECONDS = 24 * 60 * 60  # 1 day

logger = logging.getLogger(__name__)


@dataclass
class CloudUploadSettings:
    """
    The settings for uploading data into the GCP cloud storage. These apply for each individual upload. These settings
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


OrmT = TypeVar("OrmT")


def _get_content_type(orm_class: Union[Type[Images], Type[Video], Type[DicomSeries]], file_path: str) -> Optional[str]:
    if orm_class == Images:
        return mimetypes.guess_type(file_path)[0]
    elif orm_class == Video:
        return "application/octet-stream"
    elif orm_class == DicomSeries:
        return "application/dicom"
    else:
        raise ValueError(f"Unsupported type `{orm_class}`")


def upload_to_signed_url_list(
    file_paths: Iterable[str],
    config: BaseConfig,
    querier: Querier,
    orm_class: Union[Type[Images], Type[Video], Type[DicomSeries]],
    cloud_upload_settings: CloudUploadSettings,
) -> List[Union[SignedVideoURL, SignedImageURL, SignedDicomURL]]:
    """Upload files and return the upload returns in the same order as the file paths supplied."""
    failed_uploads = []
    successful_uploads = []
    for file_path in tqdm(file_paths):
        content_type = _get_content_type(orm_class, file_path)
        file_name = os.path.basename(file_path)
        signed_url = _get_signed_url(file_name, orm_class, querier)
        assert signed_url.get("title", "") == file_name, "Ordering issue"

        try:
            if cloud_upload_settings.max_retries is not None:
                max_retries = cloud_upload_settings.max_retries
            else:
                max_retries = config.requests_settings.max_retries

            if cloud_upload_settings.backoff_factor is not None:
                backoff_factor = cloud_upload_settings.backoff_factor
            else:
                backoff_factor = config.requests_settings.backoff_factor

            _upload_single_file(
                file_path, signed_url, content_type, max_retries=max_retries, backoff_factor=backoff_factor
            )
            successful_uploads.append(signed_url)
        except CloudUploadError as e:
            if cloud_upload_settings.allow_failures:
                failed_uploads.append(file_path)
            else:
                raise e

    if failed_uploads:
        logger.warning("The upload was incomplete for the following items: %s", failed_uploads)

    return successful_uploads


def upload_video_to_encord(
    signed_url: Union[SignedVideoURL, SignedImageURL, SignedDicomURL], video_title: Optional[str], querier: Querier
) -> Video:
    payload = {
        "signed_url": signed_url["signed_url"],
        "data_hash": signed_url["data_hash"],
        "title": signed_url["title"],
        "file_link": signed_url["file_link"],
        "video_title": video_title,
    }
    return querier.basic_put(
        Video,
        uid=signed_url.get("data_hash"),
        payload=payload,
        enable_logging=False,
    )


def upload_images_to_encord(
    signed_urls: List[Union[SignedVideoURL, SignedImageURL, SignedDicomURL]], querier: Querier
) -> Images:
    return querier.basic_put(Images, uid=None, payload=signed_urls, enable_logging=False)


def _get_signed_url(
    file_name: str, orm_class: Union[Type[Images], Type[Video], Type[DicomSeries]], querier: Querier
) -> Union[SignedVideoURL, SignedImageURL, SignedDicomURL]:
    if orm_class == Video:
        return querier.basic_getter(SignedVideoURL, uid=file_name)
    elif orm_class == Images:
        return querier.basic_getter(SignedImagesURL, uid=[file_name])[0]
    elif orm_class == DicomSeries:
        return querier.basic_getter(SignedDicomsURL, uid=[file_name])[0]
    raise ValueError(f"Unsupported type `{orm_class}`")


def _upload_single_file(
    file_path: str,
    signed_url: dict,
    content_type: Optional[str],
    *,
    max_retries: int,
    backoff_factor: float,
    cache_max_age: int = CACHE_DURATION_IN_SECONDS,
) -> None:
    with create_new_session(max_retries=max_retries, backoff_factor=backoff_factor) as session:
        url = signed_url["signed_url"]

        with open(file_path, "rb") as f:
            res_upload = session.put(
                url, data=f, headers={"Content-Type": content_type, "Cache-Control": f"max-age={cache_max_age}"}
            )

            if res_upload.status_code != 200:
                status_code = res_upload.status_code
                headers = res_upload.headers
                res_text = res_upload.text
                error_string = str(
                    f"Error uploading file '{signed_url.get('title', '')}' to signed url: "
                    f"'{signed_url.get('signed_url')}'.\n"
                    f"Response data:\n\tstatus code: '{status_code}'\n\theaders: '{headers}'\n\tcontent: '{res_text}'",
                )

                logger.error(error_string)
                raise RuntimeError(error_string)
