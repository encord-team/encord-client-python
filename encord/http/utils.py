import functools
import http
import logging
import mimetypes
import os.path
import urllib.error
from contextlib import contextmanager
from dataclasses import dataclass
from time import sleep
from typing import Callable, List, TypeVar, Union

import requests
from tqdm import tqdm

from encord.exceptions import CloudUploadError
from encord.http.querier import Querier
from encord.orm.dataset import (
    Images,
    SignedImagesURL,
    SignedImageURL,
    SignedVideoURL,
    Video,
)

PROGRESS_BAR_FILE_FACTOR = 100
DEFAULT_MAX_RETRIES = 5
DEFAULT_BACKOFF_FACTOR = 0.1

logger = logging.getLogger(__name__)


@dataclass
class CloudUploadSettings:
    """
    The settings for uploading data into the GCP cloud storage. These apply for each individual upload.
    """

    max_retries: int = DEFAULT_MAX_RETRIES
    """Number of allowed retries when uploading"""
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    """With each retry, there will be a sleep of backoff_factor * (retry_number + 1)"""
    allow_failures: bool = False
    """
    If failures are allowed, the upload will continue even if some items were not successfully uploaded even
    after retries. For example, upon creation of a large image group, you might want to create the image group
    even if a few images were not successfully uploaded. The unsuccessfully uploaded images will then be logged.
    """


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
    querier: Querier,
    orm_class: Union[Images, Video],
    cloud_upload_settings: CloudUploadSettings,
) -> List[Union[SignedVideoURL, SignedImageURL]]:
    if orm_class == Images:
        is_video = False
    elif orm_class == Video:
        is_video = True
    else:
        raise RuntimeError(f"Currently only `Image` or `Video` orm_class supported. Got type `{orm_class}`")

    failed_uploads = []
    successful_uploads = []
    total = len(file_paths) * PROGRESS_BAR_FILE_FACTOR
    with tqdm(total=total, desc="Files upload progress: ", leave=False) as pbar:
        for i in range(len(file_paths)):
            file_path = file_paths[i]
            file_name = os.path.basename(file_path)
            signed_url = _get_signed_url(file_name, is_video, querier)
            assert signed_url.get("title", "") == file_name, "Ordering issue"

            try:
                _upload_single_file(
                    file_path,
                    signed_url,
                    pbar,
                    is_video,
                    cloud_upload_settings.max_retries,
                    cloud_upload_settings.backoff_factor,
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


def upload_video_to_encord(signed_url: dict, querier: Querier) -> Video:
    return querier.basic_put(Video, uid=signed_url.get("data_hash"), payload=signed_url, enable_logging=False)


def upload_images_to_encord(signed_urls: List[dict], querier: Querier) -> Images:
    return querier.basic_put(Images, uid=None, payload=signed_urls, enable_logging=False)


def _get_signed_url(file_name: str, is_video: bool, querier: Querier) -> Union[SignedVideoURL, SignedImageURL]:
    if is_video:
        return querier.basic_getter(SignedVideoURL, uid=file_name)
    else:
        return querier.basic_getter(SignedImagesURL, uid=[file_name])[0]


def _upload_single_file(
    file_path: str,
    signed_url: dict,
    pbar,
    is_video: bool,
    max_retries: int,
    backoff_factor: float,
) -> None:

    res_upload = _data_upload_with_retries(file_path, signed_url, pbar, is_video, max_retries, backoff_factor)

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


"""
What I need is some sort of decorator or context manager that will wrap my code in retries
* context manager -> swallows exceptions awkwardly
* decorator => can I specify the max_retries and backoff_factor through that?
* or create an async function which is just being called blocked but where I can basically do something like
    with_retries(my_network_function(one, two, three)) -> idea is that this might only be scheduled later??
"""


def retry_network_errorrs(func: Callable):
    """
    Decorator for a function that do network requests where we would like to retry those network requests.
    The decorated function cannot use the keyword arguments `max_retries` and `backoff_factor`.
    """

    @functools.wraps(func)
    def wrapper_network_retries(*args, max_retries: int, backoff_factor: float, **kwargs):
        if max_retries < 0 or not isinstance(max_retries, int):
            raise TypeError(
                f"The max_retries argument must be a positive integer. It is currently set to `{max_retries}`"
            )
        if backoff_factor <= 0:
            raise TypeError(
                f"The back_off factor argument must be a float larger than 0. It is currently set to `{backoff_factor}"
            )

        current_backoff = backoff_factor

        for i in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (
                requests.exceptions.RequestException,
                urllib.error.URLError,
                http.client.HTTPException,
            ) as e:
                if i < max_retries:
                    logger.warning(
                        "An exception occurred during a network request. Retrying upload in %s seconds",
                        current_backoff,
                        exc_info=True,
                    )
                    sleep(current_backoff)
                    current_backoff *= 2
                else:
                    logger.exception("An exception occurred during a network request. All retries are exhausted")
                    raise e

    return wrapper_network_retries


# T = TypeVar("T")
#
#
# @contextmanager
# def retry_network_errors(network_func: T, max_retries: int, backoff_factor: float) -> T:
#     for i in range(3):
#         try:
#             yield network_func
#         except requests.exceptions.RequestException as e:
#             if i < 3:
#                 logger.warning("first error")
#                 continue
#             else:
#                 logger.error("too many retries")
#                 raise e
#
#
# def retry_network_errors2(func: Callable, func_args: list, func_kwargs: dict, max_retries: int, backoff_factor: float):
#     current_backoff = backoff_factor
#     for i in range(max_retries + 1):
#         try:
#             return func(*func_args, **func_kwargs)
#         except requests.exceptions.RequestException as e:
#             if i < max_retries:
#                 logger.warning(
#                     "An exception occurred during a network request. Retrying upload in %s seconds",
#                     current_backoff,
#                     exc_info=True,
#                 )
#                 sleep(current_backoff)
#                 current_backoff *= 2
#             else:
#                 logger.exception("An exception occurred during a network request. All retries are exhausted")
#                 raise e


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
