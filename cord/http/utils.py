import multiprocessing

import mimetypes
import logging
import os.path
from typing import List, TypeVar, Optional

import requests
import concurrent

from tqdm import tqdm

from cord.http.querier import Querier
from cord.orm.dataset import Image, Video

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

    if max_workers is None:
        max_workers = min(multiprocessing.cpu_count(), len(file_paths))
    elif max_workers < 1:
        raise ValueError(f"max_workers must be a positive integer. Received: {max_workers}")

    orm_class_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        total = len(file_paths) * PROGRESS_BAR_FILE_FACTOR
        with tqdm(total=total, desc="Files upload progress: ") as pbar:
            futures = []
            for i in range(len(file_paths)):
                file_path = file_paths[i]
                file_name = os.path.basename(file_path)
                signed_url = signed_urls[i]
                assert signed_url.get("title", "") == file_name, "Ordering issue"

                future = executor.submit(_upload_single_file, file_path, signed_url, querier, orm_class, pbar, is_video)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                orm_class_list.append(res)

    return orm_class_list


def _upload_single_file(
    file_path: str, signed_url: dict, querier: Querier, orm_class: OrmT, pbar, is_video: bool
) -> OrmT:
    content_type = "application/octet-stream" if is_video else mimetypes.guess_type(file_path)[0]
    res_upload = requests.put(
        signed_url.get("signed_url"), data=read_in_chunks(file_path, pbar), headers={"Content-Type": content_type}
    )

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
