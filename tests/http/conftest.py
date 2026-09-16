"""Shared fixtures for the HTTP-layer tests."""

import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Sequence
from unittest.mock import patch

import orjson
import pytest
import requests
from requests.adapters import HTTPAdapter


@dataclass
class MockResponse:
    """The canned HTTP reply a `MockHttpClient` serves.

    Pass `json_body` for a JSON reply, or `body` for a raw one - an HTML error page from the
    infrastructure in front of the API, say. Neither means an empty body.
    """

    status_code: int = 200
    json_body: Any = None
    body: Optional[bytes] = None
    headers: Dict[str, str] = field(default_factory=dict)

    def content(self) -> bytes:
        if self.body is not None:
            return self.body
        return orjson.dumps(self.json_body) if self.json_body is not None else b""


class MockHttpClient:
    """A stand-in transport for the SDK's API clients.

    Both clients build their own `requests` session internally, so a test cannot hand them a
    transport; this replaces `HTTPAdapter.send` instead - the last hop before the network, which
    leaves the genuine `requests` response plumbing and everything the SDK layers on top of it in
    play. Set the reply with `respond_with`; outgoing requests are recorded on `sent_requests`.

    Replacing the adapter takes the session's retry policy out of the picture, so every request
    reaching here is served the same reply, once. Tests that care about retrying assert on the
    policy itself instead.
    """

    def __init__(self) -> None:
        self.sent_requests: List[requests.PreparedRequest] = []
        self._response = MockResponse()

    def respond_with(self, response: MockResponse) -> "MockHttpClient":
        self._response = response
        return self

    def send(self, request: requests.PreparedRequest, **kwargs: Any) -> requests.Response:
        self.sent_requests.append(request)

        response = requests.Response()
        response.status_code = self._response.status_code
        response.request = request
        response.url = request.url or ""
        response.headers.update(self._response.headers)
        response._content = self._response.content()
        return response


@pytest.fixture
def mock_http_client():
    client = MockHttpClient()
    with patch.object(HTTPAdapter, "send", new=client.send):
        yield client


class _QueuedResponseHandler(BaseHTTPRequestHandler):
    """Serves the next queued reply, whatever the method or path."""

    def do_GET(self) -> None:
        self._respond()

    def do_POST(self) -> None:
        self._respond()

    def do_PUT(self) -> None:
        self._respond()

    def do_PATCH(self) -> None:
        self._respond()

    def do_DELETE(self) -> None:
        self._respond()

    def _respond(self) -> None:
        content_length = int(self.headers.get("Content-Length") or 0)
        if content_length:
            self.rfile.read(content_length)  # drain, so the connection stays reusable

        canned = self.server.take_next_response(self.command)  # type: ignore[attr-defined]
        body = canned.content()

        self.send_response(canned.status_code)
        for name, value in canned.headers.items():
            self.send_header(name, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        """Silence the default stderr access log."""


class QueuedResponseServer(ThreadingHTTPServer):
    """A real HTTP server on localhost that serves queued replies, one per request.

    `MockHttpClient` stands in above urllib3, which takes the session's retry policy out of the
    picture — so it cannot observe retrying at all. Retries only happen over a socket, so a test
    that cares whether a request was retried has to make real ones. Every request is recorded on
    `handled_methods`, which is what makes the number of attempts assertable; once the queue is
    exhausted the last reply repeats.

    Keep `Retry-After` out of any reply that is meant to be retried: urllib3 honours it by
    sleeping for exactly that long, which would put real seconds into the suite.
    """

    def __init__(self, responses: Sequence[MockResponse]) -> None:
        super().__init__(("127.0.0.1", 0), _QueuedResponseHandler)
        self._responses = list(responses) or [MockResponse()]
        self.handled_methods: List[str] = []

    @property
    def domain(self) -> str:
        host, port = self.server_address[0], self.server_address[1]
        return f"http://{host}:{port}"

    def take_next_response(self, method: str) -> MockResponse:
        self.handled_methods.append(method)
        return self._responses[min(len(self.handled_methods) - 1, len(self._responses) - 1)]


@pytest.fixture
def queued_response_server(monkeypatch):
    """Start a `QueuedResponseServer` serving `responses`, and stop it when the test ends."""
    # The SDK applies the environment's proxy settings to its requests; localhost must not go
    # through one, or these tests would depend on whatever proxy the developer happens to run.
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")

    servers: List[QueuedResponseServer] = []

    def start(*responses: MockResponse) -> QueuedResponseServer:
        server = QueuedResponseServer(responses)
        servers.append(server)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server

    try:
        yield start
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
