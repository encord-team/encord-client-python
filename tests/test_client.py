import os
import uuid

import pytest

import encord.exceptions
from encord.client import EncordClient
from encord.configs import EncordConfig
from encord.orm.label_row import LabelRow
from encord.orm.project import Project
from encord.utilities.benchmark_utilities import LabelAnnotationMetrics
from tests.test_data.img_group_test_blurb import IMG_GROUP_TEST_BLURB
from tests.test_data.interpolation_test_blurb import INTERPOLATION_TEST_BLURB

# from tests.test_data.test_blurb import TEST_BLURB

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
    return EncordClient.initialise(resource_id=keys[0], api_key=keys[1])


@pytest.fixture
def projects():
    client1 = EncordClient.initialise(os.getenv("CONSENSUS_PROJECT1_ID"), os.getenv("CONSENSUS_PROJECT1_API_KEY"))
    client2 = EncordClient.initialise(os.getenv("CONSENSUS_PROJECT2_ID"), os.getenv("CONSENSUS_PROJECT2_API_KEY"))
    client3 = EncordClient.initialise(os.getenv("CONSENSUS_PROJECT3_ID"), os.getenv("CONSENSUS_PROJECT3_API_KEY"))
    return [client1, client2, client3]


def test_initialise(keys):
    assert isinstance(EncordClient.initialise(resource_id=keys[0], api_key=keys[1]), EncordClient)


@pytest.mark.skip(reason="test not maintained")
def test_initialise_with_config(keys):
    config = EncordConfig(resource_id=keys[0], api_key=keys[1])
    assert isinstance(EncordClient.initialise_with_config(config), EncordClient)


def test_missing_key(keys):
    with pytest.raises(expected_exception=encord.exceptions.AuthenticationError) as excinfo:
        EncordClient.initialise(resource_id=keys[0])

    assert excinfo.value.message == "API key not provided"


@pytest.mark.skip(reason="test not maintained")
def test_missing_resource_id(keys):
    with pytest.raises(expected_exception=encord.exceptions.AuthenticationError) as excinfo:
        EncordClient.initialise(api_key=keys[1])

    assert excinfo.value.message == "Project ID or dataset ID not provided"


@pytest.mark.skip(reason="test not maintained")
def test_invalid_key(keys):
    with pytest.raises(expected_exception=encord.exceptions.AuthenticationError):
        EncordClient.initialise(keys[0], uuid.uuid4())


@pytest.mark.skip(reason="test not maintained")
def test_invalid_resource_id(keys):
    with pytest.raises(expected_exception=encord.exceptions.AuthenticationError):
        EncordClient.initialise(uuid.uuid4(), keys[1])


def test_get_project(client):
    assert isinstance(client.get_project(), Project)


def test_get_label_blurb(keys, client):
    assert isinstance(client.get_label_row(keys[2]), LabelRow)


def test_get_label_with_invalid_id_throws_authorisation_exception(client):
    with pytest.raises(expected_exception=encord.exceptions.AuthorisationError):
        client.get_label_row("test")


@pytest.mark.skip(reason="test not maintained")
def test_get_label_with_write_key_throws_operation_not_allowed_exception(keys):
    client = EncordClient.initialise(keys[0], LABEL_WRITE_KEY)

    with pytest.raises(expected_exception=encord.exceptions.OperationNotAllowed):
        client.get_label_row(keys[2])


@pytest.mark.skip(reason="test not maintained")
def test_save_video_label_row(keys, client):
    blurb = client.save_label_row(keys[2], TEST_BLURB)
    assert blurb is True


@pytest.mark.skip(reason="test not maintained")
def test_save_img_group_label_row(keys, client):
    blurb = client.save_label_row(keys[3], IMG_GROUP_TEST_BLURB)
    assert blurb is True


@pytest.mark.skip(reason="test not maintained")
def test_save_label_with_invalid_id_throws_authorisation_exception(keys, client):
    with pytest.raises(expected_exception=encord.exceptions.AuthorisationError):
        client.save_label_row("test", TEST_BLURB)


@pytest.mark.skip(reason="test not maintained")
def test_save_label_with_read_key_throws_operation_not_allowed_exception(keys):
    client = EncordClient.initialise(keys[0], LABEL_READ_KEY)

    with pytest.raises(expected_exception=encord.exceptions.OperationNotAllowed):
        client.save_label_row(keys[2], TEST_BLURB)


@pytest.mark.skip(reason="test not maintained")
def test_object_interpolation_with_polygons(keys):
    client = EncordClient.initialise(keys[0], LABEL_READ_KEY)
    objects = client.object_interpolation(INTERPOLATION_TEST_BLURB, ["60f75ddb-aa68-4654-8c85-f6959dbb62eb"])
    assert isinstance(objects, dict)


def test_get_labels_consensus(projects):
    feature_hashes = [obj.feature_node_hash for obj in projects[0].get_project_ontology().ontology_objects]
    answers = [
        {"930994aa": LabelAnnotationMetrics(precision=10 / 10, recall=10 / 10)},
        {"930994aa": LabelAnnotationMetrics(precision=7 / 9, recall=7 / 10)},
        {"930994aa": LabelAnnotationMetrics(precision=9 / 11, recall=9 / 10)},
        {"930994aa": LabelAnnotationMetrics(precision=6 / 11, recall=6 / 7)},
    ]
    for index, project in enumerate(projects):
        consensus_score = project.get_labels_consensus(projects, feature_hashes)
        assert consensus_score == answers[index]

    # check majority consensus (1 vs 1, 2 vs 2, ..., x vs x is no consensus)
    consensus_score = projects[2].get_labels_consensus([projects[0], projects[1]], ["930994aa"])
    assert consensus_score == answers[3]
