"""The agent run token never follows a redirect off Encord's host, as requests already ensures for Authorization."""

from typing import Dict, List

import pytest
from requests import PreparedRequest, Response
from requests.adapters import BaseAdapter

from encord.http.common import HEADER_AGENT_RUN_TOKEN
from encord.http.querier import create_new_session

START_URL = "https://api.encord.com/v2/public/projects"


class _RedirectingAdapter(BaseAdapter):
    """Answers the first request with a redirect to ``location`` and records the headers of every request."""

    def __init__(self, location: str) -> None:
        super().__init__()
        self.location = location
        self.seen: List[Dict[str, str]] = []

    def send(self, request: PreparedRequest, *args, **kwargs) -> Response:  # type: ignore[override]
        self.seen.append(dict(request.headers))
        response = Response()
        response.request = request
        response.url = request.url or ""
        if len(self.seen) == 1:
            response.status_code = 302
            response.headers["Location"] = self.location
        else:
            response.status_code = 200
        response._content = b"{}"
        return response

    def close(self) -> None:
        pass


def _follow(location: str) -> Dict[str, str]:
    """Send a request carrying the token, follow its redirect, and return the redirected request's headers."""
    adapter = _RedirectingAdapter(location)
    with create_new_session(max_retries=0, backoff_factor=0, connect_retries=0) as session:
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.get(START_URL, headers={HEADER_AGENT_RUN_TOKEN: "run.token.value", "X-Other": "kept"})
    assert len(adapter.seen) == 2
    return adapter.seen[1]


def test_the_token_follows_a_redirect_on_the_same_host() -> None:
    headers = _follow("https://api.encord.com/v2/public/projects/")

    assert headers[HEADER_AGENT_RUN_TOKEN] == "run.token.value"


@pytest.mark.parametrize(
    "location",
    [
        pytest.param("https://elsewhere.example.com/collect", id="other-host"),
        pytest.param("http://api.encord.com/v2/public/projects", id="https-to-http"),
    ],
)
def test_the_token_is_dropped_when_a_redirect_leaves_encord(location: str) -> None:
    headers = _follow(location)

    assert HEADER_AGENT_RUN_TOKEN not in headers
    assert headers["X-Other"] == "kept"
