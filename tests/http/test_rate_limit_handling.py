"""Rate-limit (HTTP 429) handling in both API clients.

A rate-limited request has to surface as `RateLimitExceededError` whichever calling path it took,
but the two clients don't get there the same way. The /v2 client reads the real HTTP status. The
legacy client speaks a protocol where the API answers `HTTP 200` and puts the real status and error
in the body - except for rate limiting, which it can also report out of band as a genuine HTTP 429:
the limiter rejects some requests before the handler that would wrap them, and the infrastructure
in front of the API sheds load on its own. The session's retry policy retries that status and, once
the budget is spent, hands the last 429 back to the client, whose body carries no legacy envelope
and need not even be JSON. The legacy client used to run that response through the envelope
handling regardless and report an exhausted rate limit as a generic server error.
"""

import pytest
import requests

from encord.configs import SshConfig
from encord.exceptions import RateLimitExceededError
from encord.http.common import HEADER_CLOUD_TRACE_CONTEXT
from encord.http.constants import RequestsSettings
from encord.http.querier import Querier, create_new_session
from encord.http.v2.api_client import ApiClient
from encord.orm.analytics import CollaboratorTimer
from encord.orm.base_dto import BaseDTO
from tests.conftest import PRIVATE_KEY
from tests.http.conftest import MockResponse, QueuedResponseServer

# What the API answers with when it rejects a request before the legacy handler wraps it, and what
# the /v2 endpoints answer with throughout.
RATE_LIMITED_BODY = {"message": "Too many requests. Please try again shortly."}

# What a rate limit rejected from inside a legacy handler looks like: HTTP 200, real status in the
# body. No `Retry-After` - the envelope has no room for it.
LEGACY_RATE_LIMITED_ENVELOPE = {
    "status": 429,
    "response": ["RATE_LIMIT_ERROR"],
    "payload": "Rate limit exceeded.",
}


@pytest.fixture
def querier() -> Querier:
    return Querier(config=SshConfig(PRIVATE_KEY))


@pytest.fixture
def api_client() -> ApiClient:
    return ApiClient(config=SshConfig(PRIVATE_KEY))


@pytest.fixture(params=["legacy", "v2"])
def api_call(request, querier: Querier, api_client: ApiClient):
    """A rate-limitable call on each client, so the shared expectations are asserted for both."""
    if request.param == "legacy":
        return lambda: querier.basic_getter(object)
    return lambda: api_client.get("/", params=None, result_type=CollaboratorTimer)


def test_http_429_raises_rate_limit_exceeded_with_the_servers_retry_hint(api_call, mock_http_client):
    mock_http_client.respond_with(
        MockResponse(status_code=429, json_body=RATE_LIMITED_BODY, headers={"Retry-After": "42"})
    )

    with pytest.raises(RateLimitExceededError) as exc_info:
        api_call()

    assert exc_info.value.retry_after == 42
    assert "Retry after 42 seconds" in str(exc_info.value)


def test_http_429_without_a_retry_after_header_carries_no_hint(api_call, mock_http_client):
    mock_http_client.respond_with(MockResponse(status_code=429, json_body=RATE_LIMITED_BODY))

    with pytest.raises(RateLimitExceededError) as exc_info:
        api_call()

    assert exc_info.value.retry_after is None
    assert "Rate limit exceeded." in str(exc_info.value)


@pytest.mark.parametrize(
    "retry_after",
    [
        pytest.param("Wed, 21 Oct 2015 07:28:00 GMT", id="http-date"),
        pytest.param("", id="empty"),
        pytest.param("soon", id="not-a-number"),
        pytest.param("-1", id="negative"),
        pytest.param("1.5", id="fractional"),
    ],
)
def test_retry_after_header_that_is_not_a_delay_in_seconds_is_ignored(retry_after, api_call, mock_http_client):
    """Only the delay-in-seconds form is understood; anything else must not break the reporting."""
    mock_http_client.respond_with(
        MockResponse(status_code=429, json_body=RATE_LIMITED_BODY, headers={"Retry-After": retry_after})
    )

    with pytest.raises(RateLimitExceededError) as exc_info:
        api_call()

    assert exc_info.value.retry_after is None


def test_http_429_with_a_non_json_body_still_raises_rate_limit_exceeded(api_call, mock_http_client):
    """A load balancer shedding load answers in its own format, not the API's."""
    mock_http_client.respond_with(
        MockResponse(
            status_code=429,
            body=b"<html><head><title>429 Too Many Requests</title></head></html>",
            headers={"Content-Type": "text/html", "Retry-After": "7"},
        )
    )

    with pytest.raises(RateLimitExceededError) as exc_info:
        api_call()

    assert exc_info.value.retry_after == 7


def test_http_429_reports_the_trace_context_of_the_rejected_request(api_call, mock_http_client):
    """Rate limits are worth chasing in the server logs, so keep the request's trace id on them."""
    mock_http_client.respond_with(MockResponse(status_code=429, json_body=RATE_LIMITED_BODY))

    with pytest.raises(RateLimitExceededError) as exc_info:
        api_call()

    sent_trace_header = mock_http_client.sent_requests[0].headers[HEADER_CLOUD_TRACE_CONTEXT]
    trace_id, span_id = sent_trace_header.split(";")[0].split("/")
    assert f"trace_id='{trace_id}' span_id='{span_id}'" in str(exc_info.value)


def test_legacy_client_raises_rate_limit_exceeded_for_an_in_envelope_rate_limit(querier, mock_http_client):
    """The shape the legacy protocol uses for a rate limit rejected inside a request handler."""
    mock_http_client.respond_with(MockResponse(status_code=200, json_body=LEGACY_RATE_LIMITED_ENVELOPE))

    with pytest.raises(RateLimitExceededError) as exc_info:
        querier.basic_getter(object)

    assert "Rate limit exceeded." in str(exc_info.value)
    assert exc_info.value.retry_after is None


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda querier: querier.basic_getter(object), id="basic_getter"),
        pytest.param(lambda querier: querier.get_multiple(object), id="get_multiple"),
        pytest.param(lambda querier: querier.post_multiple(object, payload={}), id="post_multiple"),
        pytest.param(lambda querier: querier.put_multiple(object, payload={}), id="put_multiple"),
        pytest.param(lambda querier: querier.basic_setter(object, "uid", payload={}), id="basic_setter"),
        pytest.param(lambda querier: querier.basic_put(object, "uid", payload={}), id="basic_put"),
        pytest.param(lambda querier: querier.basic_delete(object, "uid"), id="basic_delete"),
    ],
)
def test_every_legacy_calling_path_raises_rate_limit_exceeded(call, querier, mock_http_client):
    """Every legacy entry point runs through the same execute step - reads and writes alike."""
    mock_http_client.respond_with(MockResponse(status_code=429, json_body=RATE_LIMITED_BODY))

    with pytest.raises(RateLimitExceededError):
        call(querier)

    assert mock_http_client.sent_requests, "expected the call to reach the transport"


def test_legacy_session_retry_policy_lets_the_final_429_through():
    """Why the client has to recognise the status itself rather than let urllib3 raise.

    The retry budget for a 429 is spent inside the session, but `raise_on_status=False` means
    urllib3 hands the last 429 response back instead of raising - leaving the client holding a
    response the legacy envelope handling cannot read.
    """
    with create_new_session(max_retries=3, backoff_factor=0.0, connect_retries=3) as session:
        retry_policy = session.get_adapter("https://api.encord.com").max_retries

    assert requests.codes.too_many_requests in retry_policy.status_forcelist
    assert retry_policy.status == 3
    assert retry_policy.raise_on_status is False


# --- Retrying, observed over a real socket ------------------------------------------------------
#
# The tests above stand in above urllib3 and so say nothing about retrying: they would all still
# pass if the retry policy were dropped entirely. What a caller actually wants from a rate limit is
# that it disappears - the client waits and gets the answer. That is only observable end to end, so
# the tests below talk to a localhost server and assert on how many requests reached it.


class _Answer(BaseDTO):
    """A minimal response type, so a successful call has something to parse."""

    value: str


LEGACY_SUCCESS_ENVELOPE = {"status": 200, "response": {"value": "ok"}}
V2_SUCCESS_BODY = {"value": "ok"}


def _rate_limited() -> MockResponse:
    """A 429 with no `Retry-After`: urllib3 sleeps for the header's value if one is present."""
    return MockResponse(status_code=429, json_body=RATE_LIMITED_BODY)


def _querier_against(server: QueuedResponseServer, *, max_retries: int) -> Querier:
    return Querier(
        config=SshConfig(
            PRIVATE_KEY,
            domain=server.domain,
            requests_settings=RequestsSettings(max_retries=max_retries, backoff_factor=0.0),
        )
    )


def _api_client_against(server: QueuedResponseServer, *, max_retries: int) -> ApiClient:
    return ApiClient(
        config=SshConfig(
            PRIVATE_KEY,
            domain=server.domain,
            requests_settings=RequestsSettings(max_retries=max_retries, backoff_factor=0.0),
        )
    )


def test_legacy_client_retries_a_rate_limit_and_returns_the_result_that_follows(queued_response_server):
    server = queued_response_server(_rate_limited(), MockResponse(json_body=LEGACY_SUCCESS_ENVELOPE))

    answer = _querier_against(server, max_retries=1).basic_getter(_Answer)

    assert answer.value == "ok", "the rate limit should have been absorbed, not surfaced"
    # The legacy protocol tunnels every operation over an HTTP POST to `/public`, carrying the
    # logical method in the body - which is why the session's retry policy has to allow POST for
    # a legacy read to be retried at all.
    assert server.handled_methods == ["POST", "POST"], "expected one retry after the 429"


def test_v2_client_retries_a_rate_limit_and_returns_the_result_that_follows(queued_response_server):
    server = queued_response_server(_rate_limited(), MockResponse(json_body=V2_SUCCESS_BODY))

    answer = _api_client_against(server, max_retries=1).get("/", params=None, result_type=_Answer)

    assert answer.value == "ok"
    assert server.handled_methods == ["GET", "GET"]


def test_legacy_client_raises_once_a_rate_limit_outlives_the_retry_budget(queued_response_server):
    """The reported bug, end to end: the budget runs out and the last 429 reaches the client."""
    server = queued_response_server(_rate_limited())

    with pytest.raises(RateLimitExceededError):
        _querier_against(server, max_retries=2).basic_getter(_Answer)

    assert server.handled_methods == ["POST", "POST", "POST"], "expected the initial request plus two retries"


def test_v2_client_raises_once_a_rate_limit_outlives_the_retry_budget(queued_response_server):
    server = queued_response_server(_rate_limited())

    with pytest.raises(RateLimitExceededError):
        _api_client_against(server, max_retries=2).get("/", params=None, result_type=_Answer)

    assert server.handled_methods == ["GET", "GET", "GET"]


def test_a_legacy_write_does_not_spend_retries_on_a_rate_limit(queued_response_server):
    """Writes opt out of retrying, so a rate limit surfaces on the first rejection.

    Worth pinning: retrying a non-idempotent write to get past a rate limit would be worse than
    reporting it.
    """
    server = queued_response_server(_rate_limited())

    with pytest.raises(RateLimitExceededError):
        _querier_against(server, max_retries=3).basic_setter(_Answer, "uid", payload={})

    assert server.handled_methods == ["POST"]
