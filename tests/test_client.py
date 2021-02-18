import uuid
import pytest

import cord.exceptions
from cord.client import CordClient
from cord.configs import CordConfig
from cord.orm.project import Project
from cord.orm.label_row import LabelRow

from tests.test_data.test_blurb import TEST_BLURB
from tests.test_data.img_group_test_blurb import IMG_GROUP_TEST_BLURB

# Dummy keys, can be used and abused
LABEL_READ_WRITE_KEY = 'Igr3RTx7B4gJbHZM0eyjOXaPr7jg22Fw22AQbYT0nQM'
LABEL_READ_KEY = 'aEfra0xAWVOsNzW7sXhGMIPzuh5FVfflS0DiuB648Ak'
LABEL_WRITE_KEY = 'cWNtJAzzlw3eBWDTMrDPJy9iAXn9eJ0sP8yRj3EVi1U'


@pytest.fixture
def keys():
    project_id = 'dd00ab81-0834-481b-9ef5-49e35f9f7b63'  # Dummy project ID
    key = LABEL_READ_WRITE_KEY  # Dummy API key with label read/write access
    label_id = '6786fa5a-3b48-4d34-a7c5-ed2ff82bd3ba'  # Dummy video label row ID
    img_group_label_id = '5fbba385-4918-4eee-85a8-8b7a2e71dd16'
    return project_id, key, label_id, img_group_label_id


@pytest.fixture
def client(keys):
    return CordClient.initialise(project_id=keys[0], api_key=keys[1])


def test_initialise(keys):
    assert isinstance(CordClient.initialise(project_id=keys[0], api_key=keys[1]), CordClient)


def test_initialise_with_config(keys):
    config = CordConfig(project_id=keys[0], api_key=keys[1])
    assert isinstance(CordClient.initialise_with_config(config), CordClient)


def test_missing_key(keys):
    with pytest.raises(expected_exception=cord.exceptions.AuthenticationError) as excinfo:
        CordClient.initialise(project_id=keys[0])

    assert excinfo.value.message == "API key not provided"


def test_missing_project_id(keys):
    with pytest.raises(expected_exception=cord.exceptions.AuthenticationError) as excinfo:
        CordClient.initialise(api_key=keys[1])

    assert excinfo.value.message == "Project ID not provided"


def test_invalid_key(keys):
    client = CordClient.initialise(keys[0], uuid.uuid4())

    with pytest.raises(expected_exception=cord.exceptions.AuthenticationError):
        client.get_project()


def test_invalid_project_id(keys):
    client = CordClient.initialise(uuid.uuid4(), keys[1])

    with pytest.raises(expected_exception=cord.exceptions.AuthenticationError):
        client.get_project()


def test_get_project(client):
    assert isinstance(client.get_project(), Project)


def test_get_label_blurb(keys, client):
    assert isinstance(client.get_label_row(keys[2]), LabelRow)


def test_get_label_with_invalid_id_throws_authorisation_exception(client):
    with pytest.raises(expected_exception=cord.exceptions.AuthorisationError):
        client.get_label_row('test')


def test_get_label_with_write_key_throws_operation_not_allowed_exception(keys):
    client = CordClient.initialise(keys[0], LABEL_WRITE_KEY)

    with pytest.raises(expected_exception=cord.exceptions.OperationNotAllowed):
        client.get_label_row(keys[2])


def test_save_video_label_row(keys, client):
    client.save_label_row(keys[2], TEST_BLURB)


def test_save_img_group_label_row(keys, client):
    client.save_label_row(keys[3], IMG_GROUP_TEST_BLURB)


def test_save_label_with_invalid_id_throws_authorisation_exception(keys, client):
    with pytest.raises(expected_exception=cord.exceptions.AuthorisationError):
        client.save_label_row('test', TEST_BLURB)


def test_save_label_with_read_key_throws_operation_not_allowed_exception(keys):
    client = CordClient.initialise(keys[0], LABEL_READ_KEY)

    with pytest.raises(expected_exception=cord.exceptions.OperationNotAllowed):
        client.save_label_row(keys[2], TEST_BLURB)
