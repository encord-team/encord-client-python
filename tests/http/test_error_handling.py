from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from requests import Response, Session

from encord.configs import SshConfig
from encord.exceptions import EncordException
from encord.http.querier import HEADER_CLOUD_TRACE_CONTEXT, Querier
from tests.fixtures import PRIVATE_KEY


@pytest.fixture
def querier():
    return Querier(config=SshConfig(PRIVATE_KEY))


@patch.object(Session, "send")
@patch("encord.exceptions.datetime", wraps=datetime)
def test_failed_http_request_prints_out_trace_id(dt: MagicMock, send: MagicMock, querier):
    fake_time = datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    dt.now.return_value = fake_time

    res = Response()
    res.status_code = 500
    send.return_value = res

    try:
        querier.basic_getter(object)
        assert False, "Should never get here, previous line is expected to raise"
    except EncordException as e:
        trace_header = send.call_args_list[0].args[0].headers[HEADER_CLOUD_TRACE_CONTEXT]
        trace_id, span_id = trace_header.split(";")[0].split("/")

        assert (
            str(e)
            == f"Error parsing JSON response:  timestamp='2023-01-01T00:00:00+00:00' trace_id='{trace_id}' span_id='{span_id}'"
        )
