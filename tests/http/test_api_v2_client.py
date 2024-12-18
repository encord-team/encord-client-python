import json
from datetime import datetime
from typing import Type, Union
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel
from requests import Session

from encord.configs import SshConfig
from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO, RootModelDTO
from tests.fixtures import PRIVATE_KEY


class TestPayload(BaseDTO):
    payload: str


class TestPayloadV2(BaseModel):
    payload: str


class TestPayloadV3(RootModelDTO[Union[TestPayloadV2, None]]):
    pass


class TestComplexPayload(BaseDTO):
    text: str
    number: float
    time: datetime


class TestComplexPayloadV2(BaseModel):
    text: str
    number: float
    time: datetime


@pytest.fixture
def api_client():
    return ApiClient(config=SshConfig(PRIVATE_KEY))


@pytest.mark.parametrize("payload_type", [TestPayload, TestPayloadV2, TestPayloadV3])
@pytest.mark.parametrize("allow_none", [False, True])
@patch.object(Session, "send")
def test_constructed_url_is_correct(
    send: MagicMock, api_client: ApiClient, payload_type: Type[TestPayload], allow_none: bool
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = None if allow_none else {"payload": "hello world"}
    mock_response.content = "null" if allow_none else json.dumps({"payload": "hello world"})
    send.return_value = mock_response

    res = [
        api_client.get("/", params=None, result_type=payload_type, allow_none=allow_none),
        api_client.get("/test", params=None, result_type=payload_type, allow_none=allow_none),
        api_client.get("/test/", params=None, result_type=payload_type, allow_none=allow_none),
        api_client.get("test/", params=None, result_type=payload_type, allow_none=allow_none),
    ]
    if allow_none:
        for r in res:
            assert r is None
    else:
        for r in res:
            assert r is not None
            if payload_type == TestPayloadV3:
                assert r.root.payload == "hello world"
            else:
                assert r.payload == "hello world"

    assert send.call_args_list[0].args[0].url == "https://api.encord.com/v2/public"
    assert send.call_args_list[1].args[0].url == "https://api.encord.com/v2/public/test"
    assert send.call_args_list[2].args[0].url == "https://api.encord.com/v2/public/test"
    assert send.call_args_list[3].args[0].url == "https://api.encord.com/v2/public/test"


@pytest.mark.parametrize("payload_type", [TestPayload, TestPayloadV2, TestPayloadV3])
@pytest.mark.parametrize("allow_none", [False, True])
@patch.object(Session, "send")
def test_payload_url_serialisation(
    send: MagicMock, api_client: ApiClient, payload_type: Type[TestPayload], allow_none: bool
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = None if allow_none else {"payload": "hello world"}
    mock_response.content = "null" if allow_none else json.dumps({"payload": "hello world"})
    send.return_value = mock_response

    expected_time = datetime.fromisoformat("2024-02-01T01:02:03+01:00")
    payload = TestComplexPayload(text="test", number=0.01, time=expected_time)

    res = api_client.get("/", params=payload, result_type=payload_type, allow_none=allow_none)
    if allow_none:
        assert res is None
    else:
        assert res is not None
        if payload_type == TestPayloadV3:
            assert res.root.payload == "hello world"
        else:
            assert res.payload == "hello world"

    assert (
        send.call_args_list[0].args[0].url
        == "https://api.encord.com/v2/public?text=test&number=0.01&time=2024-02-01T01%3A02%3A03%2B01%3A00"
    )


@pytest.mark.parametrize("payload_type", [TestPayload, TestPayloadV2, TestPayloadV3, None])
@pytest.mark.parametrize("param_type", [TestComplexPayload, TestComplexPayloadV2])
@patch.object(Session, "send")
def test_payload_body_serialisation(
    send: MagicMock,
    api_client: ApiClient,
    payload_type: Type[TestPayload],
    param_type: Type[TestComplexPayload],
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = None if payload_type is None else {"payload": "hello world"}
    mock_response.content = "null" if payload_type is None else json.dumps({"payload": "hello world"})
    send.return_value = mock_response

    expected_time = datetime.fromisoformat("2024-02-01T01:02:03+01:00")
    payload = param_type(text="test", number=0.01, time=expected_time)

    r = api_client.post("/", params=None, payload=payload, result_type=payload_type)
    if payload_type is None:
        assert r is None
    else:
        assert r is not None
        if payload_type == TestPayloadV3:
            assert r.root.payload == "hello world"
        else:
            assert r.payload == "hello world"

    assert send.call_args_list[0].args[0].url == "https://api.encord.com/v2/public"
    assert (
        send.call_args_list[0].args[0].body == b'{"text": "test", "number": 0.01, "time": "2024-02-01T01:02:03+01:00"}'
    )
