import http.client
import logging
import sys
import urllib.error

import pytest
import requests

from encord.http.utils import retry_network_errors

DEFAULT_BACKOFF_FACTOR = 0.0000001
DEFAULT_MAX_RETRIES = 3


@pytest.mark.parametrize(
    "exception",
    [requests.exceptions.ConnectionError, urllib.error.URLError, http.client.HTTPException],
)
def test_network_retries_for_failing_function(exception):
    count = 0

    @retry_network_errors
    def failing_function():
        nonlocal count
        count += 1
        raise exception("Simulated Error")

    with pytest.raises(exception):
        failing_function(max_retries=DEFAULT_MAX_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR)
    assert count == DEFAULT_MAX_RETRIES + 1


def test_network_retries_for_non_network_exception():
    count = 0

    @retry_network_errors
    def failing_function():
        nonlocal count
        if count == 0:
            count += 1
            raise requests.exceptions.ConnectionError("Simulated Error")
        else:
            raise RuntimeError("Oh no!")

    with pytest.raises(RuntimeError):
        failing_function(max_retries=DEFAULT_MAX_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR)

    assert count == 1


def test_network_retry_function_returns_successful_response():
    """Testing args and kwargs"""
    count = 0
    expected_response = "finally a response!"

    @retry_network_errors
    def partially_failing_function(response_part_one: str, response_part_two: str):
        nonlocal count
        if count == 0:
            count += 1
            raise requests.exceptions.ConnectionError("Simulated Error")
        else:
            return response_part_one + response_part_two

    actual_response = partially_failing_function(
        expected_response[:1],
        response_part_two=expected_response[1:],
        max_retries=DEFAULT_MAX_RETRIES,
        backoff_factor=DEFAULT_BACKOFF_FACTOR,
    )
    assert actual_response == expected_response
    assert count == 1
