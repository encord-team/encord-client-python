from unittest.mock import patch

import pytest

from cord.client import CordClient
from cord.orm.dataset import DatasetType, DatasetScope, DatasetAPIKey
from cord.project_ontology.classification_type import ClassificationType
from cord.project_ontology.object_type import ObjectShape
from cord.project_ontology.ontology import Ontology
from cord.user_client import CordUserClient
from cord.utilities.client_utilities import APIKeyScopes
from cord.utilities.project_user import ProjectUserRole, ProjectUser
import os

@pytest.fixture
def keys():
    #todo change private key to a test account's
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

    users = client.add_users(["ulrik.hansen@cord.tech", "eric.landau@cord.tech"], ProjectUserRole.ANNOTATOR)

    assert ProjectUser("ulrik.hansen@cord.tech", ProjectUserRole.ANNOTATOR, project_hash) in users
    assert ProjectUser("eric.landau@cord.tech", ProjectUserRole.ANNOTATOR, project_hash) in users


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
def test_update_existing_ontology(generate_feature_node_hash,keys):
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

