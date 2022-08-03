import logging
import sys
from collections import Callable

import requests

from encord.http.utils import (
    retry_network_errorrs,
    retry_network_errors,
    retry_network_errors2,
)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)s] [%(funcName)s()] %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)


def test_network_retries():
    @retry_network_errorrs
    def failing_function(some_arg: str):
        print(f"some_arg = {some_arg}")
        raise requests.exceptions.ConnectionError("Simulated ConnectionError.")

    failing_function("bla", max_retries=3, backoff_factor=0.1)


def test_network_retries_context_manager():
    def failing_function(some_arg: str):
        print(f"some_arg = {some_arg}")
        # print(f"max_retries = {max_retries}")
        # print(f"backoff_factor = {backoff_factor}")
        raise requests.exceptions.ConnectionError("Simulated ConnectionError.")

    with retry_network_errors(failing_function, max_retries=3, backoff_factor=3.3) as func:
        func("argsss")


def failing_function(some_arg: str):
    print(f"some_arg = {some_arg}")
    # print(f"max_retries = {max_retries}")
    # print(f"backoff_factor = {backoff_factor}")
    raise requests.exceptions.ConnectionError("Simulated ConnectionError.")


def test_network_retries_func():
    result = retry_network_errors2(
        failing_function, func_args=["arg"], func_kwargs={}, max_retries=3, backoff_factor=0.1
    )


def test_bla():
    async def gru(one_arg: str):
        print(one_arg)

    x = gru("my arg")
    # await x

    # def wrapper(func: Callable):
    #     func


def test_gru():
    """essentially create a decorator which just passes on the same function and makes you call it again
    so you'd need to do something like
    retrier(network_function(one, two), max_retries=5, ...)

    """

    def wrapper():
        pass
