"""Regression tests for FOU-1491."""

import inspect
from unittest.mock import patch

from urllib3.util.retry import Retry

from encord.http import querier


class _Urllib3_1xRetry:
    """Mimics urllib3 1.26.x ``Retry`` whose ``__init__`` predates ``backoff_jitter``."""

    def __init__(
        self,
        connect=None,
        read=None,
        status=None,
        other=None,
        allowed_methods=None,
        status_forcelist=None,
        backoff_factor=0,
        raise_on_status=True,
    ):
        self.kwargs = {
            "connect": connect,
            "read": read,
            "status": status,
            "other": other,
            "allowed_methods": allowed_methods,
            "status_forcelist": status_forcelist,
            "backoff_factor": backoff_factor,
            "raise_on_status": raise_on_status,
        }


def test_create_new_session_omits_backoff_jitter_on_urllib3_1x():
    querier._retry_supports_backoff_jitter.cache_clear()
    try:
        with patch.object(querier, "Retry", _Urllib3_1xRetry):
            # Before the fix this raised: TypeError: __init__() got an unexpected
            # keyword argument 'backoff_jitter'
            with querier.create_new_session(
                max_retries=3, backoff_factor=1.5, connect_retries=3, backoff_jitter=1.5
            ) as session:
                assert session is not None
    finally:
        querier._retry_supports_backoff_jitter.cache_clear()


def test_create_new_session_forwards_backoff_jitter_on_urllib3_2x():
    querier._retry_supports_backoff_jitter.cache_clear()
    try:
        has_param = "backoff_jitter" in inspect.signature(Retry.__init__).parameters
        assert has_param == querier._retry_supports_backoff_jitter()
        with querier.create_new_session(
            max_retries=3, backoff_factor=1.5, connect_retries=3, backoff_jitter=1.5
        ) as session:
            adapter = session.get_adapter("https://example.com")
            assert adapter.max_retries.backoff_jitter == 1.5
    finally:
        querier._retry_supports_backoff_jitter.cache_clear()
