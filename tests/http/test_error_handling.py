from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from requests import Response, Session

from encord.configs import ENCORD_DOMAIN, SshConfig
from encord.exceptions import EncordException, SshKeyNotFound
from encord.http.querier import HEADER_CLOUD_TRACE_CONTEXT, Querier
from tests.fixtures import PRIVATE_KEY


@pytest.fixture
def querier() -> Querier:
    return Querier(config=SshConfig(PRIVATE_KEY))


@patch.object(Session, "send")
@patch("encord.exceptions.datetime", wraps=datetime)
def test_failed_http_request_prints_out_trace_id(dt: MagicMock, send: MagicMock, querier: Querier):
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


@patch.object(Session, "send")
def test_response_error_message_including_domain(send: MagicMock, querier: Querier):
    res = Response()
    res.status_code = 400
    res._content = b'{"status":400,"response":["SSH_KEY_NOT_FOUND_ERROR"],"payload":"Your used SSH key does not exist. Please add this SSH key to your user profile."}'
    send.return_value = res

    with pytest.raises(SshKeyNotFound) as e:
        querier.basic_getter(object)
    assert ENCORD_DOMAIN in str(e)
