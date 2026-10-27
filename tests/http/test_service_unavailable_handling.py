"""Platform-down (HTTP 502/503/504) handling in both API clients.

When the service is down, restarting or overloaded, the load balancer in front of the API answers
on its behalf - typically with an HTML page and no JSON envelope. Both clients raise a
`ServiceUnavailableError` naming the status, so the caller knows to retry later rather than seeing
an unknown error or a JSON-parse failure.
"""

import pytest

from encord.configs import SshConfig
from encord.exceptions import ServiceUnavailableError, UnknownException
from encord.http.querier import Querier
from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO
from tests.conftest import PRIVATE_KEY
from tests.http.conftest import MockResponse

GOOGLE_LB_502_PAGE = (
    b"<html><head><title>502 Server Error</title></head><body><h1>Error: Server Error</h1>"
    b"<h2>The server encountered a temporary error and could not complete your request.</h2></body></html>"
)


class _Answer(BaseDTO):
    value: str


@pytest.fixture(params=["legacy", "v2"])
def api_call(request):
    if request.param == "legacy":
        querier = Querier(config=SshConfig(PRIVATE_KEY))
        return lambda: querier.basic_getter(_Answer, "uid")
    api_client = ApiClient(config=SshConfig(PRIVATE_KEY))
    return lambda: api_client.get("/", params=None, result_type=_Answer)


@pytest.mark.parametrize("status_code", [502, 503, 504])
@pytest.mark.parametrize(
    "body",
    [
        pytest.param(GOOGLE_LB_502_PAGE, id="html_error_page"),
        pytest.param(b"", id="empty_body"),
        pytest.param(b"upstream connect error or disconnect/reset before headers", id="plain_text"),
    ],
)
def test_platform_down_raises_service_unavailable(status_code, body, api_call, mock_http_client):
    mock_http_client.respond_with(MockResponse(status_code=status_code, body=body))

    with pytest.raises(ServiceUnavailableError) as exc_info:
        api_call()

    message = str(exc_info.value)
    assert "temporarily unavailable" in message
    assert f"HTTP {status_code}" in message
    assert "trace_id=" in message
    assert exc_info.value.status_code == status_code


def test_v2_other_unknown_statuses_keep_the_generic_message(mock_http_client):
    """Statuses outside the outage set still raise a plain `UnknownException`, message unchanged."""
    api_client = ApiClient(config=SshConfig(PRIVATE_KEY))
    mock_http_client.respond_with(MockResponse(status_code=500, body=b"<html>oops</html>"))

    with pytest.raises(UnknownException) as exc_info:
        api_client.get("/", params=None, result_type=_Answer)

    assert not isinstance(exc_info.value, ServiceUnavailableError)
    assert exc_info.value.message == "An unknown error occurred."
