"""Tests for TLS/CA-bundle handling on outgoing requests.

The SDK's two API clients issue prepared requests through ``Session.send``,
which — unlike ``Session.request`` — does not run
``merge_environment_settings``. Without applying those settings at the send
sites, the ``REQUESTS_CA_BUNDLE`` / ``CURL_CA_BUNDLE`` environment variables
are silently ignored and verification falls back to certifi, breaking any
deployment behind a TLS-inspecting proxy (FOU-1493).

These tests assert at the ``HTTPAdapter.send`` boundary — the point where
``requests`` hands over the fully resolved ``verify`` value — so they cover
the real resolution chain rather than our own plumbing.
"""

import json
from unittest.mock import patch

import pytest
import requests
from requests.adapters import HTTPAdapter

from encord.user_client import EncordUserClient
from tests.conftest import PRIVATE_KEY_PEM

# Reuse the response routing from the timeout tests; the hashes just route the stubs.
from tests.http.test_timeout_overrides_setting import DATASET_HASH, PROJECT_HASH, stub_responses


@pytest.fixture(autouse=True)
def _clear_ca_env(monkeypatch):
    """Start every test from a known state — no CA env vars set."""
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)


@pytest.fixture
def ca_bundle(monkeypatch, tmp_path):
    """A CA-bundle path exposed via REQUESTS_CA_BUNDLE, as behind a corporate proxy."""
    bundle = tmp_path / "corporate-ca.pem"
    bundle.write_text("")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(bundle))
    return str(bundle)


def _adapter_stub(captured_verify):
    """An HTTPAdapter.send replacement that records the resolved ``verify``.

    Builds real ``Response`` objects (from the shared routing stub) because —
    unlike ``Session.send`` patching — the response continues through the
    genuine ``Session.send`` post-processing.
    """

    def send(request, **kwargs):
        captured_verify.append(kwargs.get("verify"))
        response = requests.Response()
        response.status_code = 200
        response.request = request
        response._content = json.dumps(stub_responses(request).json.return_value).encode()
        return response

    return send


def _exercise_both_api_clients():
    user_client = EncordUserClient.create_with_ssh_private_key(ssh_private_key=PRIVATE_KEY_PEM)
    user_client.get_project(PROJECT_HASH)  # v2 api_client path
    user_client.get_dataset(DATASET_HASH).list_data_rows()  # legacy querier path


@patch.object(HTTPAdapter, "send")
def test_api_clients_honour_requests_ca_bundle_env(adapter_send, ca_bundle):
    captured_verify = []
    adapter_send.side_effect = _adapter_stub(captured_verify)

    _exercise_both_api_clients()

    assert len(captured_verify) >= 2, "expected requests from both the v2 client and the legacy querier"
    assert all(verify == ca_bundle for verify in captured_verify)


@patch.object(HTTPAdapter, "send")
def test_api_clients_default_to_certifi_without_env(adapter_send):
    captured_verify = []
    adapter_send.side_effect = _adapter_stub(captured_verify)

    _exercise_both_api_clients()

    assert len(captured_verify) >= 2
    assert all(verify is True for verify in captured_verify)


@patch.object(HTTPAdapter, "send")
def test_signed_url_upload_honours_requests_ca_bundle_env(adapter_send, ca_bundle, tmp_path):
    """Uploads go through ``session.put`` (i.e. ``Session.request``), which merges
    environment settings natively — pin that this stays true."""
    from encord.http.utils import _upload_single_file

    captured_verify = []

    def send(request, **kwargs):
        captured_verify.append(kwargs.get("verify"))
        response = requests.Response()
        response.status_code = 200
        response.request = request
        return response

    adapter_send.side_effect = send

    upload_file = tmp_path / "payload.txt"
    upload_file.write_text("data")
    _upload_single_file(
        str(upload_file),
        title="payload.txt",
        signed_url="https://signed.example/payload.txt",
        content_type="text/plain",
        max_retries=0,
        backoff_factor=0.0,
    )

    assert captured_verify == [ca_bundle]
