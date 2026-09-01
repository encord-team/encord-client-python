from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from encord.configs import BearerConfig, SshConfig, UserConfig
from encord.http.v2.api_client import ApiClient
from encord.ml_models_client import MlModelsClient
from tests.conftest import PRIVATE_KEY

DOMAIN = "https://api.example.com"
MODEL_UUID = UUID("00000000-0000-0000-0000-000000000001")

# A domain is routinely supplied with a trailing slash, and every URL builder in the SDK reads
# ``Config.domain``. Each of these must be equivalent to the canonical, slash-free form.
DOMAIN_VARIANTS = [DOMAIN, f"{DOMAIN}/", f"{DOMAIN}//"]


@pytest.mark.parametrize("domain", DOMAIN_VARIANTS)
def test_domain_is_stored_without_trailing_slash(domain: str) -> None:
    assert SshConfig(PRIVATE_KEY, domain=domain).domain == DOMAIN


@pytest.mark.parametrize("domain", DOMAIN_VARIANTS)
def test_legacy_endpoint_has_a_single_leading_slash(domain: str) -> None:
    assert SshConfig(PRIVATE_KEY, domain=domain).endpoint == f"{DOMAIN}/public"


@pytest.mark.parametrize("domain", DOMAIN_VARIANTS)
def test_user_endpoint_has_a_single_leading_slash(domain: str) -> None:
    config = UserConfig(SshConfig(PRIVATE_KEY, domain=domain))

    assert config.endpoint == f"{DOMAIN}/public/user"
    assert config.domain == DOMAIN


@pytest.mark.parametrize("domain", DOMAIN_VARIANTS)
def test_v2_url_is_unaffected_by_a_trailing_slash(domain: str) -> None:
    client = ApiClient(config=SshConfig(PRIVATE_KEY, domain=domain))

    assert client._build_url("/projects/abc") == f"{DOMAIN}/v2/public/projects/abc"


@pytest.mark.parametrize("domain", DOMAIN_VARIANTS)
@patch.object(ApiClient, "_request")
def test_ml_endpoint_url_is_built_from_the_normalized_domain(request: MagicMock, domain: str) -> None:
    # ``api/ml_endpoints.py`` bypasses ``_build_url`` and interpolates the domain directly.
    client = MlModelsClient(ApiClient(config=SshConfig(PRIVATE_KEY, domain=domain)))

    client.get_model(model_uuid=MODEL_UUID)

    assert request.call_args.args[0].url == f"{DOMAIN}/v2/public/ml-models/{MODEL_UUID}"


@pytest.mark.parametrize("domain", DOMAIN_VARIANTS)
def test_bearer_config_normalizes_the_domain_too(domain: str) -> None:
    config = BearerConfig.from_bearer_token("token", domain=domain)

    assert config.domain == DOMAIN
    assert config.endpoint == f"{DOMAIN}/public"
