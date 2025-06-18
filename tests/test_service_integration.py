from unittest.mock import Mock
from uuid import uuid4

import pytest

from encord import EncordUserClient
from encord.exceptions import TokenVerificationError
from encord.service_integration import _JSONWebKey, _JSONWebKeySet


@pytest.fixture
def jwks() -> _JSONWebKeySet:
    key = _JSONWebKey(
        kid="4051a39d-4e03-46ab-9375-e5d5ca0fa5d4",
        kty="OKP",
        crv="Ed25519",
        alg="EdDSA",
        use="sig",
        x="TVH-J_caZCqNm_OKrQMGPwUJo1IetRXxA-QeEReYfbs",
    )
    return _JSONWebKeySet(keys=[key])


@pytest.fixture
def encord_client(monkeypatch, jwks) -> EncordUserClient:
    stub_api_client = Mock()
    stub_api_client.get.return_value = jwks

    client = EncordUserClient(config=Mock(), querier=Mock())
    client._api_client = stub_api_client

    return client


def test_verify_token_succeeds_when_jwt_is_valid(encord_client):
    valid_jwt_no_expiry = "eyJhbGciOiJFZERTQSIsImtpZCI6IjQwNTFhMzlkLTRlMDMtNDZhYi05Mzc1LWU1ZDVjYTBmYTVkNCIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJodHRwOi8vMC4wLjAuMDo4MDAxIiwiaWF0IjoxNzUwMjUwNDEzLjA3MjQ1NSwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo2OTY5Iiwic3ViIjoiZWR3YXJkQGVuY29yZC5jb20ifQ.D05IMAU4iYmRpyeDRVGueq85WQIBUhK_Yq7Sy6v2MWHc_sxy7L2HxJHBDA9hK_Jim27XnRY41OD0HJVYR0DlBQ"

    service_integration = encord_client.get_service_integration(uuid=uuid4())
    verified = service_integration.verify_token(token=valid_jwt_no_expiry)

    assert verified.aud == "http://0.0.0.0:8001"
    assert verified.iat == 1750250413.072455
    assert verified.iss == "http://localhost:6969"
    assert verified.sub == "edward@encord.com"


def test_verify_token_fails_when_jwt_has_expired(encord_client):
    expired_jwt = "eyJhbGciOiJFZERTQSIsImtpZCI6IjQwNTFhMzlkLTRlMDMtNDZhYi05Mzc1LWU1ZDVjYTBmYTVkNCIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJodHRwOi8vMC4wLjAuMDo4MDAxIiwiZXhwIjoxNzUwMjUwNzcwLjY4NTc2NCwiaWF0IjoxNzUwMjUwNzY5LjY4NTc2NCwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo2OTY5Iiwic3ViIjoiZWR3YXJkQGVuY29yZC5jb20ifQ.5pp2NofuPCXJ25fAoWllIFFpH4eSJExUupzQTOrDSypGxUdZ6vLDV1g7Sv_ZgENawbL1MahnR6WzX6SqCJGKBQ"

    service_integration = encord_client.get_service_integration(uuid=uuid4())
    with pytest.raises(TokenVerificationError) as exc:
        service_integration.verify_token(token=expired_jwt)

    assert exc.value.message == "JWT has expired."


def test_verify_token_fails_when_jwt_has_no_jwk_in_jwks(encord_client):
    jwt_no_matching_key = "eyJhbGciOiJFZERTQSIsImtpZCI6IjQwNTFhMzlkLTRlMDMtNDZhYi05Mzc0LWU1ZDVjYTBmYTVkNCIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJodHRwOi8vMC4wLjAuMDo4MDAxIiwiZXhwIjoxNzUwMjUxMjc1LjQ3NDUzNywiaWF0IjoxNzUwMjUxMjc0LjQ3NDUzNywiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo2OTY5Iiwic3ViIjoiZWR3YXJkQGVuY29yZC5jb20ifQ.58vLylouZ2P3bbMdeWHZ_TM3gAsod5AgxSzIi7oQzXArq4xnu3zbHfZHgTyDl43fqd5fUXKcLD0QJHYXy37PAw"

    service_integration = encord_client.get_service_integration(uuid=uuid4())
    with pytest.raises(TokenVerificationError) as exc:
        service_integration.verify_token(token=jwt_no_matching_key)

    assert exc.value.message == "Token could not be verified using any of the service integration's keys."


def test_verify_token_fails_when_jwt_has_no_key_id_in_header(encord_client):
    jwt_no_key_id = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJodHRwOi8vMC4wLjAuMDo4MDAxIiwiZXhwIjoxNzUwMjU0MDAwLjkwNjg4NywiaWF0IjoxNzUwMjUzOTQwLjkwNjg4NywiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo2OTY5Iiwic3ViIjoiZWR3YXJkQGVuY29yZC5jb20ifQ.uBY-ptKBGTuwL27_q04_cutJgF7S2gKGe0RIwu9UvGLW20VkwDCPciHSMjUkkW4FiHL_QO4ko5wUTAiUTuL4DA"

    service_integration = encord_client.get_service_integration(uuid=uuid4())
    with pytest.raises(TokenVerificationError) as exc:
        service_integration.verify_token(token=jwt_no_key_id)

    assert exc.value.message == "Token header does not include a key id."
