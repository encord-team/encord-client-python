from datetime import datetime
from unittest.mock import patch

import pytest

from cord.client import CordClient, CordClientProject
from cord.constants.model import FASTER_RCNN
from cord.constants.model_weights import faster_rcnn_R_50_DC5_1x, faster_rcnn_R_101_FPN_3x
from cord.orm.dataset import DatasetType, DatasetScope, DatasetAPIKey
from cord.orm.label_log import LabelLog
from cord.orm.model import ModelTrainingWeights
from cord.project_ontology.classification_type import ClassificationType
from cord.project_ontology.object_type import ObjectShape
from cord.project_ontology.ontology import Ontology
from cord.user_client import CordUserClient
from cord.utilities import label_utilities
from cord.utilities.client_utilities import APIKeyScopes
from cord.utilities.project_user import ProjectUserRole, ProjectUser
import os

# create template project and use this in tests where i don't need to directly test create project funcitonality

# create some cleanup where everything that was created gets removed afterwards (maybe do this on the backend)

TRAINING_BATCH_SIZE = 5
TRAINING_EPOCH_SIZE = 1


@pytest.fixture
def keys():
    private_key = os.environ.get("PRIVATE_KEY")
    cord_user_endpoint = 'http://127.0.0.1:8000/public/user'
    cord_endpoint = 'http://127.0.0.1:8000/public'

    return private_key, cord_user_endpoint, cord_endpoint


def get_expected_project_ontology():
    ontology = Ontology()
    ontology.add_object("box", ObjectShape.BOUNDING_BOX)
    ontology.add_object("polygon", ObjectShape.POLYGON)
    ontology.add_classification("checklist", ClassificationType.CHECKLIST, True, ["a", "b", "c"])
    ontology.add_classification("radio", ClassificationType.RADIO, False, ["d", "e", "f"])
    ontology.add_classification("text", ClassificationType.TEXT, False)

    return ontology


def get_dummy_feature_node_hash():
    return "76db1793"


def get_template_project_with_labels(endpoint):
    # TODO put these as environmental variables
    client = CordClient.initialise(
        '1c57a760-acd9-4be4-a005-c3ef37e0968e',  # Project ID
        'AlcEk3k8oelAZ-jZJJj1WsgbA6RaGFzAIWU6O4WjAqo',  # API key
        endpoint=endpoint
    )
    return client


def get_template_project_feature_hashes():
    # TODO put this in an environmental variable or parameterise this somehow
    return ["6b2736fc"]


# TODO put this in an environmental variable
def get_template_dataset_hash():
    return "3da4f875-f612-4f00-8927-2cb1c3d5bda7"


def get_label_hash(client: CordClientProject):
    project = client.get_project()
    label_rows = project["label_rows"][0]
    return label_rows["label_hash"]


def get_data_hash(client: CordClientProject):
    project = client.get_project()
    label_rows = project["label_rows"][0]
    return label_rows["data_hash"]


def test_create_project_with_no_datasets(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)

    project_hash = user_client.create_project("test project", [], "")

    assert isinstance(project_hash, str)


def test_create_project_api_key(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    project_hash = user_client.create_project("test project with api key", [], "")

    api_key = user_client.create_project_api_key(project_hash, "test api key", [scope for scope in APIKeyScopes])

    assert isinstance(api_key, str)


def test_get_project_api_keys(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    project_hash = user_client.create_project("test project with api key", [], "")
    api_key_1 = user_client.create_project_api_key(project_hash, "test api key",
                                                   [APIKeyScopes.LABEL_READ, APIKeyScopes.LABEL_WRITE])
    api_key_2 = user_client.create_project_api_key(project_hash, "test api key",
                                                   [APIKeyScopes.LABEL_READ, APIKeyScopes.ALGO_LIBRARY])

    all_api_keys = user_client.get_project_api_keys(project_hash)
    all_api_keys = [api_key.api_key for api_key in all_api_keys]

    assert api_key_1 in all_api_keys
    assert api_key_2 in all_api_keys


def test_create_dataset(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    dataset_title = "test dataset"
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    dataset = user_client.create_dataset(dataset_title, DatasetType.CORD_STORAGE)

    assert isinstance(dataset, dict)
    assert dataset["title"] == dataset_title
    assert dataset["type"] == DatasetType.CORD_STORAGE
    assert isinstance(dataset["dataset_hash"], str)


def test_create_dataset_api_key(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    dataset = user_client.create_dataset("test dataset", DatasetType.CORD_STORAGE)
    dataset_hash = dataset["dataset_hash"]

    api_key = user_client.create_dataset_api_key(dataset_hash, "test api key", [scope for scope in DatasetScope])

    assert isinstance(api_key, DatasetAPIKey)
    assert isinstance(api_key.api_key, str)


def test_get_dataset_api_keys(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    dataset = user_client.create_dataset("test dataset", DatasetType.CORD_STORAGE)
    dataset_hash = dataset["dataset_hash"]
    api_key_1 = user_client.create_dataset_api_key(dataset_hash, "test api key", [DatasetScope.READ])
    api_key_2 = user_client.create_dataset_api_key(dataset_hash, "test api key", [DatasetScope.WRITE])

    all_api_keys = user_client.get_dataset_api_keys(dataset_hash)

    assert api_key_1 in all_api_keys
    assert api_key_2 in all_api_keys


def test_add_datasets_to_project(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    cord_client_endpoint = keys[2]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    dataset_1 = user_client.create_dataset("test dataset1", DatasetType.CORD_STORAGE)
    dataset_2 = user_client.create_dataset("test dataset1", DatasetType.AWS)
    dataset_1_hash = dataset_1["dataset_hash"]
    dataset_2_hash = dataset_2["dataset_hash"]
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_client_endpoint)

    result = client.add_datasets([dataset_1_hash, dataset_2_hash])

    assert result


def test_remove_datasets_datasets_from_project(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    cord_client_endpoint = keys[2]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    dataset_1 = user_client.create_dataset("test dataset1", DatasetType.CORD_STORAGE)
    dataset_2 = user_client.create_dataset("test dataset1", DatasetType.AWS)
    dataset_1_hash = dataset_1["dataset_hash"]
    dataset_2_hash = dataset_2["dataset_hash"]
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_client_endpoint)
    client.add_datasets([dataset_1_hash, dataset_2_hash])

    result = client.remove_datasets([dataset_1_hash])

    assert result


def test_add_users_to_project(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    cord_client_endpoint = keys[2]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_client_endpoint)

    users = client.add_users(["testuser1@cord.tech", "testuser2@cord.tech"], ProjectUserRole.ANNOTATOR)

    assert ProjectUser("testuser1@cord.tech", ProjectUserRole.ANNOTATOR, project_hash) in users
    assert ProjectUser("testuser2@cord.tech", ProjectUserRole.ANNOTATOR, project_hash) in users


def test_show_empty_project_ontology(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    cord_client_endpoint = keys[2]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_client_endpoint)

    ontology = client.get_project_ontology()

    assert ontology.to_dict() == Ontology().to_dict()


@patch('cord.project_ontology.ontology.generate_feature_node_hash')
def test_update_existing_ontology(generate_feature_node_hash, keys):
    generate_feature_node_hash.return_value = get_dummy_feature_node_hash()
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    cord_client_endpoint = keys[2]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_client_endpoint)

    client.add_object("box", ObjectShape.BOUNDING_BOX)
    client.add_object("polygon", ObjectShape.POLYGON)
    client.add_classification("checklist", ClassificationType.CHECKLIST, True, ["a", "b", "c"])
    client.add_classification("radio", ClassificationType.RADIO, False, ["d", "e", "f"])
    client.add_classification("text", ClassificationType.TEXT, False)

    ontology = client.get_project_ontology()
    expected_ontology = get_expected_project_ontology()

    assert ontology.to_dict() == expected_ontology.to_dict()


def test_get_label_row(keys):
    cord_client_endpoint = keys[2]
    client = get_template_project_with_labels(cord_client_endpoint)
    label_hash = get_label_hash(client)

    label_row = client.get_label_row(label_hash)

    assert label_row["data_units"].keys()


def test_save_label_row(keys):
    cord_client_endpoint = keys[2]
    client = get_template_project_with_labels(cord_client_endpoint)
    label_hash = get_label_hash(client)
    label_row = client.get_label_row(label_hash)
    label_row_dict = label_utilities.construct_answer_dictionaries(label_row)

    save_result = client.save_label_row(label_hash, label_row_dict)

    assert save_result


def test_create_label_row(keys):
    private_key = keys[0]
    cord_user_endpoint = keys[1]
    cord_client_endpoint = keys[2]
    user_client = CordUserClient.create_with_ssh_private_key(private_key, endpoint=cord_user_endpoint)
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])

    client = CordClient.initialise(project_hash, project_api_key, cord_client_endpoint)
    client.add_datasets([get_template_dataset_hash()])
    data_hash = get_data_hash(client)

    label_row = client.create_label_row(data_hash)

    assert label_row["data_units"].keys()


def test_create_model_row(keys):
    cord_client_endpoint = keys[2]
    client = get_template_project_with_labels(cord_client_endpoint)
    feature_hashes = get_template_project_feature_hashes()

    model_hash = client.create_model_row(title='Test model',
                                         description='A test model',
                                         features=feature_hashes,
                                         model=FASTER_RCNN)
    delete_result = client.model_delete(model_hash)

    assert isinstance(model_hash, str)
    assert delete_result


def test_get_label_logs(keys):
    cord_client_endpoint = keys[2]
    client = get_template_project_with_labels(cord_client_endpoint)
    data_hash = get_data_hash(client)

    label_logs = client.get_label_logs(data_hash=data_hash)

    assert len(label_logs) > 0
    assert isinstance(label_logs[0], LabelLog)


def test_model_train(keys):
    cord_client_endpoint = keys[2]
    client = get_template_project_with_labels(cord_client_endpoint)
    feature_hashes = get_template_project_feature_hashes()
    label_hash = get_label_hash(client)
    model_hash = client.create_model_row(title='Test model',
                                         description='A test model',
                                         features=feature_hashes,
                                         model=FASTER_RCNN)

    model_train = client.model_train(model_hash, [label_hash], TRAINING_EPOCH_SIZE, TRAINING_BATCH_SIZE,
                                         faster_rcnn_R_101_FPN_3x, device="cpu")
    delete_result = client.model_delete(model_hash)

    assert model_train["status"]
    assert isinstance(model_train["response"][0]["training_hash"], str)


#todo
def test_model_inference(keys):
    pass
