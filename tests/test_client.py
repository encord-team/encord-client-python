from unittest.mock import MagicMock

import pytest

from encord.client import EncordClient
from encord.exceptions import AuthenticationError, AuthorisationError
from encord.orm.label_row import LabelRow
from encord.orm.project import Project

# Dummy keys, can be used and abused
LABEL_READ_WRITE_KEY = "Igr3RTx7B4gJbHZM0eyjOXaPr7jg22Fw22AQbYT0nQM"
LABEL_READ_KEY = "aEfra0xAWVOsNzW7sXhGMIPzuh5FVfflS0DiuB648Ak"
LABEL_WRITE_KEY = "cWNtJAzzlw3eBWDTMrDPJy9iAXn9eJ0sP8yRj3EVi1U"


@pytest.fixture
def keys():
    resource_id = "dd00ab81-0834-481b-9ef5-49e35f9f7b63"  # Dummy project ID
    key = LABEL_READ_WRITE_KEY  # Dummy API key with label read/write access
    label_id = "6786fa5a-3b48-4d34-a7c5-ed2ff82bd3ba"  # Dummy video label row ID
    img_group_label_id = "5fbba385-4918-4eee-85a8-8b7a2e71dd16"  # Image group label row ID
    return resource_id, key, label_id, img_group_label_id


@pytest.fixture
def client(keys):
    return EncordClient(
        querier=MagicMock(),
        config=MagicMock(),
        api_client=MagicMock(),
    )


def test_get_project(client):
    assert isinstance(client.get_project(), Project)


def test_get_label_blurb(keys, client):
    assert isinstance(client.get_label_row(keys[2]), LabelRow)


def test_get_label_with_invalid_id_throws_authorisation_exception(client):
    with pytest.raises(expected_exception=AuthorisationError):
        client.get_label_row("test")
