"""Payload-too-large (HTTP 413) handling in both API clients.

The sibling of the rate-limit case in `test_rate_limit_handling.py`, and the same root cause: the
legacy protocol answers `HTTP 200` with the real status in the body, but the payload limit trips
while the request body is still being read - before the handler that would wrap the error - so it
comes back as a real HTTP 413 with no envelope. The legacy client used to run that response through
the envelope handling, find no error in it, and report an unknown one.
"""

import pytest

from encord.configs import SshConfig
from encord.exceptions import PayloadTooLargeError
from encord.http.constants import RequestsSettings
from encord.http.querier import Querier
from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO
from tests.conftest import PRIVATE_KEY
from tests.http.conftest import MockResponse

# What the API answers with when the payload limit trips: FastAPI's shape, naming the limit.
PAYLOAD_TOO_LARGE_BODY = {"detail": "Request payload exceeds 2147483648 bytes limit"}

# The same message in the API's own error shape, which names it `message` rather than `detail`.
PAYLOAD_TOO_LARGE_BODY_WITH_MESSAGE = {"message": PAYLOAD_TOO_LARGE_BODY["detail"]}

GENERIC_MESSAGE = "Request payload is too large and exceeds the maximum allowed size."


class _Answer(BaseDTO):
    value: str


@pytest.fixture
def querier() -> Querier:
    return Querier(config=SshConfig(PRIVATE_KEY))


@pytest.fixture
def api_client() -> ApiClient:
    return ApiClient(config=SshConfig(PRIVATE_KEY))


@pytest.fixture(params=["legacy", "v2"])
def api_call(request, querier: Querier, api_client: ApiClient):
    """A call on each client, so the shared expectations are asserted for both."""
    if request.param == "legacy":
        return lambda: querier.basic_setter(_Answer, "uid", payload={"big": "payload"})
    return lambda: api_client.post("/", params=None, payload=None, result_type=_Answer)


@pytest.mark.parametrize(
    "json_body",
    [
        pytest.param(PAYLOAD_TOO_LARGE_BODY, id="detail"),
        pytest.param(PAYLOAD_TOO_LARGE_BODY_WITH_MESSAGE, id="message"),
    ],
)
def test_http_413_raises_payload_too_large_naming_the_limit(json_body, api_call, mock_http_client):
    """Both clients pass the server's message on: the limit it enforced is the useful part.

    It reaches them under `detail` from a handler answering before the envelope wrapper, and under
    `message` from the API's own error shape. Both are read, so both are asserted here - covering
    only one would let the other regress to a sentence that names no limit.
    """
    mock_http_client.respond_with(MockResponse(status_code=413, json_body=json_body))

    with pytest.raises(PayloadTooLargeError) as exc_info:
        api_call()

    assert "2147483648 bytes limit" in str(exc_info.value)


@pytest.mark.parametrize(
    "response",
    [
        pytest.param(
            MockResponse(
                status_code=413,
                body=b"<html><head><title>413 Request Entity Too Large</title></head></html>",
                headers={"Content-Type": "text/html"},
            ),
            id="html_error_page",
        ),
        pytest.param(MockResponse(status_code=413), id="empty_body"),
        pytest.param(MockResponse(status_code=413, body=b"null"), id="json_null"),
        pytest.param(MockResponse(status_code=413, body=b"[]"), id="json_array"),
    ],
)
def test_http_413_without_a_message_falls_back_to_a_generic_message(response, api_call, mock_http_client):
    """None of these carries a message to pass on, so the caller gets the generic sentence.

    A proxy rejecting the upload answers in its own format, and a body can be absent altogether.
    The JSON cases are the ones worth pinning: `null` and `[]` parse, so reading a message off them
    is what the legacy helper's dictionary guard prevents - without it they would raise an
    `AttributeError` from inside the 413 branch instead of falling back.
    """
    mock_http_client.respond_with(response)

    with pytest.raises(PayloadTooLargeError) as exc_info:
        api_call()

    assert GENERIC_MESSAGE in str(exc_info.value)


def test_http_413_reports_the_request_trace_context(api_call, mock_http_client):
    mock_http_client.respond_with(MockResponse(status_code=413, json_body=PAYLOAD_TOO_LARGE_BODY))

    with pytest.raises(PayloadTooLargeError) as exc_info:
        api_call()

    assert "trace_id=" in str(exc_info.value)


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda querier: querier.basic_getter(_Answer), id="basic_getter"),
        pytest.param(lambda querier: querier.get_multiple(_Answer), id="get_multiple"),
        pytest.param(lambda querier: querier.post_multiple(_Answer, payload={}), id="post_multiple"),
        pytest.param(lambda querier: querier.put_multiple(_Answer, payload={}), id="put_multiple"),
        pytest.param(lambda querier: querier.basic_setter(_Answer, "uid", payload={}), id="basic_setter"),
        pytest.param(lambda querier: querier.basic_put(_Answer, "uid", payload={}), id="basic_put"),
        pytest.param(lambda querier: querier.basic_delete(_Answer, "uid"), id="basic_delete"),
    ],
)
def test_every_legacy_calling_path_raises_payload_too_large(call, querier, mock_http_client):
    mock_http_client.respond_with(MockResponse(status_code=413, json_body=PAYLOAD_TOO_LARGE_BODY))

    with pytest.raises(PayloadTooLargeError):
        call(querier)

    assert mock_http_client.sent_requests, "expected the call to reach the transport"


def test_a_payload_too_large_is_re_sent_before_it_surfaces(queued_response_server):
    """Documents a cost this change does not address: 413 sits in the session's `status_forcelist`.

    So an over-sized body is uploaded `max_retries` more times before the caller is told, and no
    amount of retrying can make the same payload fit. Dropping 413 from that list would fix it, but
    the list is shared with the /v2 client and every other 413 source, so it is left alone here.
    """
    server = queued_response_server(MockResponse(status_code=413, json_body=PAYLOAD_TOO_LARGE_BODY))
    querier = Querier(
        config=SshConfig(
            PRIVATE_KEY,
            domain=server.domain,
            requests_settings=RequestsSettings(max_retries=2, backoff_factor=0.0),
        )
    )

    with pytest.raises(PayloadTooLargeError):
        querier.basic_getter(_Answer)

    assert server.handled_methods == ["POST", "POST", "POST"]
