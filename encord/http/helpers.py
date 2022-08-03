import functools
import http.client
import logging
import urllib.error
from time import sleep
from typing import Callable

import requests

logger = logging.getLogger(__name__)


def retry_on_network_errors(func: Callable):
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
                    logger.exception(
                        "An exception occurred during a network request. All retries are exhausted.", exc_info=True
                    )
                    raise e

    return wrapper_network_retries
