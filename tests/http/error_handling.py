from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from requests import Response, Session

from encord.configs import UserConfig
from encord.exceptions import EncordException
from encord.http.querier import HEADER_CLOUD_TRACE_CONTEXT, Querier

PRIVATE_KEY = Ed25519PrivateKey.generate()


@pytest.fixture
def querier():
    return Querier(config=UserConfig(PRIVATE_KEY))


@patch.object(Session, "send")
@patch("encord.exceptions.datetime", wraps=datetime)
def test_response_without_trace_headers_handled_correctly(dt: MagicMock, send: MagicMock, querier):
    fake_time = datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    dt.now.return_value = fake_time

    res = Response()
    res.status_code = 500
    send.return_value = res

    try:
        querier.basic_getter(object)
        assert False, "Should never get here, previous line is expected to raise"
    except EncordException as e:
        assert str(e) == "Error parsing JSON response:  timestamp='2023-01-01T00:00:00+00:00'"


@patch.object(Session, "send")
@patch("encord.exceptions.datetime", wraps=datetime)
def test_response_with_trace_id_only_handled_correctly(dt: MagicMock, send: MagicMock, querier):
    fake_time = datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    dt.now.return_value = fake_time

    res = Response()
    res.status_code = 500
    res.headers = {HEADER_CLOUD_TRACE_CONTEXT: "6ac3bbd569934be395d87090bd4857d9"}
    send.return_value = res

    try:
        querier.basic_getter(object)
        assert False, "Should never get here, previous line is expected to raise"
    except EncordException as e:
        assert (
            str(e)
            == "Error parsing JSON response:  timestamp='2023-01-01T00:00:00+00:00' trace_id='6ac3bbd569934be395d87090bd4857d9'"
        )


@patch.object(Session, "send")
@patch("encord.exceptions.datetime", wraps=datetime)
def test_response_with_trace_id_and_span_id_handled_correctly(dt: MagicMock, send: MagicMock, querier):
    fake_time = datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    dt.now.return_value = fake_time

    res = Response()
    res.status_code = 500
    res.headers = {HEADER_CLOUD_TRACE_CONTEXT: "6ac3bbd569934be395d87090bd4857d9/727472342"}
    send.return_value = res

    try:
        querier.basic_getter(object)
        assert False, "Should never get here, previous line is expected to raise"
    except EncordException as e:
        assert (
            str(e)
            == "Error parsing JSON response:  timestamp='2023-01-01T00:00:00+00:00' trace_id='6ac3bbd569934be395d87090bd4857d9' span_id='727472342'"
        )


@patch.object(Session, "send")
@patch("encord.exceptions.datetime", wraps=datetime)
def test_response_with_full_tracing_header_handled_correctly(dt: MagicMock, send: MagicMock, querier):
    fake_time = datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    dt.now.return_value = fake_time

    res = Response()
    res.status_code = 500
    res.headers = {HEADER_CLOUD_TRACE_CONTEXT: "6ac3bbd569934be395d87090bd4857d9/727472342;o=1"}
    send.return_value = res

    try:
        querier.basic_getter(object)
        assert False, "Should never get here, previous line is expected to raise"
    except EncordException as e:
        assert (
            str(e)
            == "Error parsing JSON response:  timestamp='2023-01-01T00:00:00+00:00' trace_id='6ac3bbd569934be395d87090bd4857d9' span_id='727472342'"
        )
