"""The agent run token reaches Encord on every request, from whichever request path and credential type sends it.

Agents share one client across the runs they handle, so the token is read per request and must follow the provider.
"""

from typing import Callable, List, Optional

import pytest
from requests import PreparedRequest, Request

from encord.configs import BaseConfig, BearerConfig, Config, SshConfig, UserConfig
from encord.http.common import HEADER_AGENT_RUN_TOKEN
from encord.http.constants import RequestsSettings
from tests.conftest import PRIVATE_KEY

DOMAIN = "https://api.example.com"


def _configs(settings: RequestsSettings) -> List[Config]:
    return [
        SshConfig(PRIVATE_KEY, domain=DOMAIN, requests_settings=settings),
        BearerConfig("user-token", domain=DOMAIN, requests_settings=settings),
    ]


def _v1_headers(config: BaseConfig) -> dict:
    return config.define_headers(resource_id=None, resource_type=None, data="{}")


def _v2_headers(config: BaseConfig) -> dict:
    request = Request("POST", f"{DOMAIN}/v2/public/projects", data=b"{}").prepare()
    return dict(config.define_headers_v2(request).headers)


HEADER_BUILDERS: List[Callable[[BaseConfig], dict]] = [_v1_headers, _v2_headers]


@pytest.mark.parametrize("build_headers", HEADER_BUILDERS, ids=["v1", "v2"])
@pytest.mark.parametrize("config_index", [0, 1], ids=["ssh", "bearer"])
def test_the_run_token_is_sent_when_a_provider_supplies_one(
    build_headers: Callable[[BaseConfig], dict], config_index: int
) -> None:
    config = _configs(RequestsSettings(agent_run_token_provider=lambda: "run.token.value"))[config_index]

    assert build_headers(config)[HEADER_AGENT_RUN_TOKEN] == "run.token.value"


@pytest.mark.parametrize("build_headers", HEADER_BUILDERS, ids=["v1", "v2"])
@pytest.mark.parametrize("config_index", [0, 1], ids=["ssh", "bearer"])
@pytest.mark.parametrize(
    "provider",
    [None, lambda: None, lambda: ""],
    ids=["no-provider", "provider-returns-none", "provider-returns-empty"],
)
def test_no_run_token_header_without_a_token(
    build_headers: Callable[[BaseConfig], dict],
    config_index: int,
    provider: Optional[Callable[[], Optional[str]]],
) -> None:
    """Clients that never set a token send exactly the headers they sent before."""
    config = _configs(RequestsSettings(agent_run_token_provider=provider))[config_index]

    assert HEADER_AGENT_RUN_TOKEN not in build_headers(config)


@pytest.mark.parametrize("build_headers", HEADER_BUILDERS, ids=["v1", "v2"])
def test_the_token_is_read_for_each_request(build_headers: Callable[[BaseConfig], dict]) -> None:
    """A client shared across runs sends whichever run's token is current, not the one it was created with."""
    current = {"token": "first-run"}
    config = SshConfig(
        PRIVATE_KEY,
        domain=DOMAIN,
        requests_settings=RequestsSettings(agent_run_token_provider=lambda: current["token"]),
    )

    first = build_headers(config)[HEADER_AGENT_RUN_TOKEN]
    current["token"] = "second-run"
    second = build_headers(config)[HEADER_AGENT_RUN_TOKEN]

    assert (first, second) == ("first-run", "second-run")


def test_user_endpoint_requests_carry_the_token() -> None:
    settings = RequestsSettings(agent_run_token_provider=lambda: "run.token.value")
    config = UserConfig(SshConfig(PRIVATE_KEY, domain=DOMAIN, requests_settings=settings))

    assert _v1_headers(config)[HEADER_AGENT_RUN_TOKEN] == "run.token.value"
    assert _v2_headers(config)[HEADER_AGENT_RUN_TOKEN] == "run.token.value"


def test_the_token_does_not_replace_the_callers_own_credentials() -> None:
    """The token rides beside the SSH signature or bearer token; it never stands in for them."""
    settings = RequestsSettings(agent_run_token_provider=lambda: "run.token.value")
    ssh = SshConfig(PRIVATE_KEY, domain=DOMAIN, requests_settings=settings)
    bearer = BearerConfig("user-token", domain=DOMAIN, requests_settings=settings)

    assert _v1_headers(ssh)["Authorization"].startswith(ssh.public_key_hex + ":")
    assert "Signature" in _v2_headers(ssh)
    assert _v1_headers(bearer)["Authorization"] == "Bearer user-token"
    assert _v2_headers(bearer)["Authorization"] == "Bearer user-token"


def test_v2_ssh_signature_is_unchanged_by_the_token() -> None:
    """The v2 signature covers the method, path and body only, so adding the header cannot break verification."""

    def signed(settings: RequestsSettings) -> PreparedRequest:
        request = Request("POST", f"{DOMAIN}/v2/public/projects", data=b"{}").prepare()
        return SshConfig(PRIVATE_KEY, domain=DOMAIN, requests_settings=settings).define_headers_v2(request)

    with_token = signed(RequestsSettings(agent_run_token_provider=lambda: "run.token.value"))
    without_token = signed(RequestsSettings())

    assert (
        with_token.headers["Signature-Input"].split(";created=")[0]
        == (without_token.headers["Signature-Input"].split(";created=")[0])
    )
