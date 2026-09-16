"""Long-polling upload jobs treat a rate limit as the transient failure it is.

The polling loops absorb a bounded number of failed requests so a week-long upload job is not
abandoned over one bad response. A rate limit belongs in that set: it says "come back later", which
is exactly what the loop does. It also says *when* - and with only
`LONG_POLLING_RESPONSE_RETRY_N` attempts to spend, returning before the bucket has refilled would
burn the budget without ever succeeding.
"""

from unittest.mock import MagicMock, patch

import pytest

from encord.client import (
    LONG_POLLING_RESPONSE_RETRY_N,
    LONG_POLLING_SLEEP_ON_FAILURE_SECONDS,
    EncordClientDataset,
)
from encord.configs import SshConfig
from encord.exceptions import RateLimitExceededError
from encord.orm.dataset import LongPollingStatus
from tests.conftest import PRIVATE_KEY

_DONE_RESPONSE = MagicMock(
    status=LongPollingStatus.DONE,
    units_pending_count=0,
    units_done_count=1,
    units_error_count=0,
    units_cancelled_count=0,
)


@pytest.fixture
def dataset_client() -> EncordClientDataset:
    return EncordClientDataset(
        querier=MagicMock(),
        config=SshConfig(PRIVATE_KEY),
        api_client=MagicMock(),
    )


@pytest.fixture
def sleep():
    """Patch out the wait, and record what it was asked to sleep for."""
    with patch("encord.client.time.sleep") as mock_sleep:
        yield mock_sleep


def test_a_rate_limited_poll_is_retried_rather_than_ending_the_job(dataset_client, sleep):
    dataset_client._querier.basic_getter.side_effect = [
        RateLimitExceededError(retry_after=None),
        _DONE_RESPONSE,
    ]

    result = dataset_client.add_private_data_to_dataset_get_result("upload-job-id")

    assert result is _DONE_RESPONSE, "the rate limit should have been absorbed, not surfaced"
    assert dataset_client._querier.basic_getter.call_count == 2
    sleep.assert_called_once_with(LONG_POLLING_SLEEP_ON_FAILURE_SECONDS)


def test_a_rate_limited_poll_waits_as_long_as_the_server_asked(dataset_client, sleep):
    """Anything shorter would spend the retry budget before the bucket has refilled."""
    retry_after = LONG_POLLING_SLEEP_ON_FAILURE_SECONDS * 6
    dataset_client._querier.basic_getter.side_effect = [
        RateLimitExceededError(retry_after=retry_after),
        _DONE_RESPONSE,
    ]

    dataset_client.add_private_data_to_dataset_get_result("upload-job-id")

    sleep.assert_called_once_with(retry_after)


def test_a_shorter_hint_than_the_default_wait_does_not_shorten_it(dataset_client, sleep):
    dataset_client._querier.basic_getter.side_effect = [
        RateLimitExceededError(retry_after=1),
        _DONE_RESPONSE,
    ]

    dataset_client.add_private_data_to_dataset_get_result("upload-job-id")

    sleep.assert_called_once_with(LONG_POLLING_SLEEP_ON_FAILURE_SECONDS)


def test_a_rate_limit_that_outlives_the_retry_budget_surfaces(dataset_client, sleep):
    """The loop is patient, not infinitely so - the caller still gets told in the end."""
    dataset_client._querier.basic_getter.side_effect = RateLimitExceededError(retry_after=30)

    with pytest.raises(RateLimitExceededError):
        dataset_client.add_private_data_to_dataset_get_result("upload-job-id")

    assert dataset_client._querier.basic_getter.call_count == LONG_POLLING_RESPONSE_RETRY_N
