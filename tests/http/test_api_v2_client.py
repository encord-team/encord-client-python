from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from requests import Response, Session

from encord.configs import SshConfig, UserConfig
from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO

PRIVATE_KEY = Ed25519PrivateKey.generate()


class TestPayload(BaseDTO):
    payload: str


class TestComplexPayload(BaseDTO):
    text: str
    number: float
    time: datetime


@pytest.fixture
def api_client():
    return ApiClient(config=SshConfig(PRIVATE_KEY))


@patch.object(Session, "send")
def test_constructed_url_is_correct(send: MagicMock, api_client: ApiClient):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"payload": "hello world"}
    send.return_value = mock_response

    api_client.get("/", params=None, result_type=TestPayload)
    api_client.get("/test", params=None, result_type=TestPayload)
    api_client.get("/test/", params=None, result_type=TestPayload)
    api_client.get("test/", params=None, result_type=TestPayload)

    assert send.call_args_list[0].args[0].url == "https://api.encord.com/v2/public"
    assert send.call_args_list[1].args[0].url == "https://api.encord.com/v2/public/test"
    assert send.call_args_list[2].args[0].url == "https://api.encord.com/v2/public/test"
    assert send.call_args_list[3].args[0].url == "https://api.encord.com/v2/public/test"


@patch.object(Session, "send")
def test_payload_url_serialisation(send: MagicMock, api_client: ApiClient):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"payload": "hello world"}
    send.return_value = mock_response

    expected_time = datetime.fromisoformat("2024-02-01T01:02:03+01:00")
    payload = TestComplexPayload(text="test", number=0.01, time=expected_time)

    api_client.get("/", params=payload, result_type=TestPayload)

    assert (
        send.call_args_list[0].args[0].url
        == "https://api.encord.com/v2/public?text=test&number=0.01&time=2024-02-01T01%3A02%3A03%2B01%3A00"
    )


@patch.object(Session, "send")
def test_payload_body_serialisation(send: MagicMock, api_client: ApiClient):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"payload": "hello world"}
    send.return_value = mock_response

    expected_time = datetime.fromisoformat("2024-02-01T01:02:03+01:00")
    payload = TestComplexPayload(text="test", number=0.01, time=expected_time)

    api_client.post("/", params=None, payload=payload, result_type=TestPayload)

    assert send.call_args_list[0].args[0].url == "https://api.encord.com/v2/public"
    assert (
        send.call_args_list[0].args[0].body == b'{"text": "test", "number": 0.01, "time": "2024-02-01T01:02:03+01:00"}'
    )
