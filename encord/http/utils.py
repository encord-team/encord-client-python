import logging
import mimetypes
import multiprocessing
import os.path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from time import sleep
from typing import List, Optional, TypeVar

import requests
from requests.adapters import HTTPAdapter, Retry
from tqdm import tqdm

from encord.exceptions import UploadError
from encord.http.querier import Querier
from encord.orm.dataset import Image, Video

PROGRESS_BAR_FILE_FACTOR = 100

logger = logging.getLogger(__name__)


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

# DENIS: deprecate max workers
def upload_to_signed_url_list(
    file_paths: List[str], signed_urls, querier: Querier, orm_class: OrmT, max_workers: Optional[int] = None
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
                res = _upload_single_file(file_path, signed_url, querier, orm_class, pbar, is_video)
                orm_class_list.append(res)
            except UploadError:
                # DENIS: for special exceptions
                failed_uploads.append(file_path)  # DENIS: return this.

    return orm_class_list


def _upload_single_file(
    file_path: str,
    signed_url: dict,
    querier: Querier,
    orm_class: OrmT,
    pbar,
    is_video: bool,
) -> OrmT:
    # s = requests.Session()
    # retries = Retry(
    #     total=5,
    #     backoff_factor=2,
    # )
    # s.mount("https://", HTTPAdapter(max_retries=retries))

    # content_type = "application/octet-stream" if is_video else mimetypes.guess_type(file_path)[0]
    # res_upload = requests.put(
    #     signed_url.get("signed_url"), data=read_in_chunks(file_path, pbar), headers={"Content-Type": content_type}
    # )

    # DENIS: these are arguments
    # max_retries = 5
    # backoff_factor = 0.1
    #
    # current_backoff = backoff_factor
    # for i in range(max_retries):
    #     try:
    #         res_upload = requests.put(
    #             # "https://blabla.cosdf",
    #             signed_url.get("signed_url"),
    #             data=read_in_chunks(file_path, pbar),
    #             headers={"Content-Type": content_type},
    #         )
    #         break
    #     except Exception as e:
    #         if i < max_retries - 1:
    #             logger.warning(
    #                 "An exception occurred during the file upload. Will retry in %s seconds",
    #                 current_backoff,
    #                 exc_info=True,
    #             )
    #             sleep(current_backoff)
    #             current_backoff *= 2
    # else:
    #     raise UploadError("")
    res_upload = _data_upload_with_retries(file_path, signed_url, pbar, is_video)

    if res_upload.status_code == 200:
        data_hash = signed_url.get("data_hash")

        res = querier.basic_put(orm_class, uid=data_hash, payload=signed_url, enable_logging=False)

        if not orm_class(res):
            logger.info("Error uploading: %s", signed_url.get("title", ""))

    else:
        error_string = (
            f"Error uploading file '{signed_url.get('title', '')}' to signed url: " f"'{signed_url.get('signed_url')}'",
        )
        logger.error(error_string)
        raise RuntimeError(error_string)

    return orm_class(res)


def _data_upload_with_retries(
    file_path: str,
    signed_url: dict,
    pbar,
    is_video: bool,
):
    content_type = "application/octet-stream" if is_video else mimetypes.guess_type(file_path)[0]

    max_retries = 5
    backoff_factor = 0.1

    current_backoff = backoff_factor
    for i in range(max_retries):
        try:
            return requests.put(
                # "https://blabla.cosdf",
                signed_url.get("signed_url"),
                data=read_in_chunks(file_path, pbar),
                headers={"Content-Type": content_type},
            )
        except Exception as e:
            if i < max_retries - 1:
                logger.warning(
                    "An exception occurred during the file upload. Retrying upload in %s seconds",
                    current_backoff,
                    exc_info=True,
                )
                sleep(current_backoff)
                current_backoff *= 2

    raise UploadError("")
