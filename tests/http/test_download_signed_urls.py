from contextlib import contextmanager
from unittest.mock import patch

import requests

import encord.http.utils as utils
from encord.http.constants import RequestsSettings
from encord.http.utils import download_signed_urls_as_json


class _FakeResponse:
    def __init__(self, status_code: int, body=None, raise_json: bool = False):
        self.status_code = status_code
        self._body = body
        self._raise_json = raise_json

    def json(self):
        if self._raise_json:
            raise ValueError("not valid json")
        return self._body


class _FakeSession:
    """Routes each URL to a canned response, or raises a configured exception."""

    def __init__(self, routes, raises=None):
        self._routes = routes
        self._raises = raises or {}

    def get(self, url, timeout=None):
        if url in self._raises:
            raise self._raises[url]
        return self._routes[url]


def _run(routes, urls, raises=None):
    session = _FakeSession(routes, raises)

    @contextmanager
    def fake_create_new_session(**_kwargs):
        yield session

    with patch.object(utils, "create_new_session", fake_create_new_session):
        return download_signed_urls_as_json(urls, requests_settings=RequestsSettings())


def test_resolves_successful_urls():
    routes = {
        "https://a": _FakeResponse(200, {"k": "a"}),
        "https://b": _FakeResponse(200, {"k": "b"}),
    }
    result = _run(routes, ["https://a", "https://b"])
    assert result == {"https://a": {"k": "a"}, "https://b": {"k": "b"}}


def test_omits_non_200_status():
    routes = {
        "https://ok": _FakeResponse(200, {"k": "v"}),
        "https://missing": _FakeResponse(404),
    }
    result = _run(routes, ["https://ok", "https://missing"])
    assert result == {"https://ok": {"k": "v"}}


def test_omits_unparseable_body():
    routes = {
        "https://ok": _FakeResponse(200, {"k": "v"}),
        "https://garbage": _FakeResponse(200, raise_json=True),
    }
    result = _run(routes, ["https://ok", "https://garbage"])
    assert result == {"https://ok": {"k": "v"}}


def test_omits_url_that_raises_request_exception():
    routes = {"https://ok": _FakeResponse(200, {"k": "v"})}
    raises = {"https://boom": requests.ConnectionError("reset")}
    result = _run(routes, ["https://ok", "https://boom"], raises=raises)
    assert result == {"https://ok": {"k": "v"}}


def test_dedups_and_ignores_falsy_urls():
    routes = {"https://ok": _FakeResponse(200, {"k": "v"})}
    result = _run(routes, ["https://ok", "https://ok", "", None])
    assert result == {"https://ok": {"k": "v"}}


def test_empty_input_does_no_work():
    # create_new_session must never be called when there are no URLs.
    with patch.object(utils, "create_new_session", side_effect=AssertionError("should not fetch")):
        assert download_signed_urls_as_json([], requests_settings=RequestsSettings()) == {}
        assert download_signed_urls_as_json(["", None], requests_settings=RequestsSettings()) == {}  # type: ignore[list-item]
