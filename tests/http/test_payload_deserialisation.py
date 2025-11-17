from unittest.mock import MagicMock, patch

import pytest
from requests import Response, Session

from encord.configs import SshConfig
from encord.exceptions import EncordException
from encord.http.v2.api_client import ApiClient
from encord.orm.analytics import CollaboratorTimer
from tests.fixtures import PRIVATE_KEY


@pytest.fixture
def api_client():
    return ApiClient(config=SshConfig(PRIVATE_KEY))


@patch.object(Session, "send")
def test_deserialise_payload_raises_on_wrong_payload(send: MagicMock, api_client: ApiClient):
    res = Response()
    res.status_code = 200
    res._content = b'{ "some_wrong_key": "some_wrong_value" }'
    send.return_value = res

    with pytest.raises(EncordException):
        api_client.get("/", params=None, result_type=CollaboratorTimer)


@patch.object(Session, "send")
def test_deserialise_payload_ok_on_correct_payload(send: MagicMock, api_client: ApiClient):
    res = Response()
    res.status_code = 200
    res._content = b"""
    {
        "user_email": "noone@nowhere.com",
        "user_role": 0,
        "data_title": "some title"  ,
        "time_seconds": 123.456
    }
    """
    send.return_value = res

    res = api_client.get("/", params=None, result_type=CollaboratorTimer)

    assert isinstance(res, CollaboratorTimer)
    assert res == CollaboratorTimer(
        user_email="noone@nowhere.com", user_role=0, data_title="some title", time_seconds=123.456
    )


@patch.object(Session, "send")
def test_deserialise_payload_ok_on_extra_keys(send: MagicMock, api_client: ApiClient):
    res = Response()
    res.status_code = 200
    res._content = b"""
    {
        "user_email": "noone@nowhere.com",
        "user_role": 0,
        "data_title": "some title",
        "time_seconds": 123.456,
        "extra_key": "extra_value"
    }
    """
    send.return_value = res

    res = api_client.get("/", params=None, result_type=CollaboratorTimer)

    assert isinstance(res, CollaboratorTimer)
    assert res == CollaboratorTimer(
        user_email="noone@nowhere.com", user_role=0, data_title="some title", time_seconds=123.456
    )
