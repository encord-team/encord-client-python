import logging
import mimetypes
import os.path
from dataclasses import dataclass
from time import sleep
from typing import List, TypeVar

import requests
from tqdm import tqdm

from encord.exceptions import CloudUploadError
from encord.http.querier import Querier
from encord.orm.dataset import Image, Video

PROGRESS_BAR_FILE_FACTOR = 100

logger = logging.getLogger(__name__)


@dataclass
class CloudUploadSettings:
    """
    The settings for uploading data into the GCP cloud storage. These apply for each individual upload.
    """

    # Number of allowed retries when uploading
    max_retries: int = 5
    # With each retry, there will be a sleep of backoff_factor * (retry_number + 1)
    backoff_factor: float = 0.1
    # If failures are allowed, the upload will continue even if some items were not successfully uploaded even
    # after retries. For example, upon creation of a large image group, you might want to create the image group
    # even if a few images were not successfully uploaded. The unsuccessfully uploaded images will then be logged.
    allow_failures: bool = False


def read_in_chunks(file_path, pbar, blocksize=1024, chunks=-1):
    """Splitting the file into chunks."""
    with open(file_path, "rb") as file_object:
        size = os.path.getsize(file_path)
        current = 0
        while chunks:
            data = file_object.read(blocksize)
            if not data:
                break
            yield data
            chunks -= 1
            step = round(blocksize / size * PROGRESS_BAR_FILE_FACTOR, 1)
            current = min(PROGRESS_BAR_FILE_FACTOR, current + step)
            pbar.update(min(PROGRESS_BAR_FILE_FACTOR - current, step))


OrmT = TypeVar("OrmT")


def upload_to_signed_url_list(
    file_paths: List[str],
    signed_urls,
    querier: Querier,
    orm_class: OrmT,
    cloud_upload_settings: CloudUploadSettings,
) -> List[OrmT]:
    if orm_class == Image:
        is_video = False
    elif orm_class == Video:
        is_video = True
    else:
        raise RuntimeError(f"Currently only `Image` or `Video` orm_class supported. Got type `{orm_class}`")

    assert len(file_paths) == len(signed_urls), "Error getting the correct number of signed urls"

    failed_uploads = []
    orm_class_list = []
    total = len(file_paths) * PROGRESS_BAR_FILE_FACTOR
    with tqdm(total=total, desc="Files upload progress: ") as pbar:
        for i in range(len(file_paths)):
            file_path = file_paths[i]
            file_name = os.path.basename(file_path)
            signed_url = signed_urls[i]
            assert signed_url.get("title", "") == file_name, "Ordering issue"

            try:
                res = _upload_single_file(
                    file_path,
                    signed_url,
                    querier,
                    orm_class,
                    pbar,
                    is_video,
                    cloud_upload_settings.max_retries,
                    cloud_upload_settings.backoff_factor,
                )
                orm_class_list.append(res)
            except CloudUploadError as e:
                if cloud_upload_settings.allow_failures:
                    failed_uploads.append(file_path)
                else:
                    raise e

    if failed_uploads:
        logger.warning("The upload was incomplete for the following items: %s", failed_uploads)

    return orm_class_list


def _upload_single_file(
    file_path: str,
    signed_url: dict,
    querier: Querier,
    orm_class: OrmT,
    pbar,
    is_video: bool,
    max_retries: int,
    backoff_factor: float,
) -> OrmT:

    res_upload = _data_upload_with_retries(file_path, signed_url, pbar, is_video, max_retries, backoff_factor)

    if res_upload.status_code == 200:
        data_hash = signed_url.get("data_hash")

        res = querier.basic_put(orm_class, uid=data_hash, payload=signed_url, enable_logging=False)

        if not orm_class(res):
            logger.info("Error uploading: %s", signed_url.get("title", ""))

    else:
        status_code = res_upload.status_code
        headers = res_upload.headers
        res_text = res_upload.text
        error_string = (
            f"Error uploading file '{signed_url.get('title', '')}' to signed url: "
            f"'{signed_url.get('signed_url')}'.\n"
            f"Response data: status code: '{status_code}', headers: '{headers}', content: '{res_text}'",
        )
        logger.error(error_string)
        raise RuntimeError(error_string)

    return orm_class(res)


def _data_upload_with_retries(
    file_path: str,
    signed_url: dict,
    pbar,
    is_video: bool,
    max_retries: int,
    backoff_factor: float,
):
    content_type = "application/octet-stream" if is_video else mimetypes.guess_type(file_path)[0]

    current_backoff = backoff_factor
    for i in range(max_retries + 1):
        try:
            return requests.put(
                signed_url.get("signed_url"),
                data=read_in_chunks(file_path, pbar),
                headers={"Content-Type": content_type},
            )
        except Exception:
            if i < max_retries:
                logger.warning(
                    "An exception occurred during uploading the file `%s`. Retrying upload in %s seconds",
                    file_path,
                    current_backoff,
                    exc_info=True,
                )
                sleep(current_backoff)
                current_backoff *= 2
            else:
                logger.exception("An exception occurred during uploading the file `%s`", file_path)

    raise CloudUploadError("Could not upload a file. Please check the logs for details.")
