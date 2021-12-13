import os
from datetime import datetime
from unittest.mock import patch

import pytest

from cord.client import CordClient
from cord.constants.model import FASTER_RCNN
from cord.constants.model_weights import faster_rcnn_R_101_FPN_3x
from cord.orm.dataset import DatasetType, DatasetScope, DatasetAPIKey
from cord.orm.label_log import LabelLog
from cord.project_ontology.classification_type import ClassificationType
from cord.project_ontology.object_type import ObjectShape
from cord.project_ontology.ontology import Ontology
from cord.user_client import CordUserClient
from cord.utilities import label_utilities
from cord.utilities.client_utilities import APIKeyScopes
from cord.utilities.project_user import ProjectUserRole, ProjectUser
from sdk_tests.test_data.project_tests_constants import *


def assert_empty_labels_rows_equal(real_label_row, dummy_label_row):
    keys_to_check = ('dataset_title', 'data_title', 'data_type', 'label_status', 'object_answers',
                     'classification_answers', 'object_actions')
    data_units_keys_to_check = ('data_title', 'data_type', 'data_fps', 'width', 'height', 'data_sequence',)
    for key in keys_to_check:
        assert real_label_row[key] == dummy_label_row[key]

    real_data_units_key = list(real_label_row["data_units"].keys())[0]
    dummy_data_units_key = list(dummy_label_row["data_units"].keys())[0]

    for key in data_units_keys_to_check:
        assert real_label_row["data_units"][real_data_units_key][key] == \
               dummy_label_row["data_units"][dummy_data_units_key][key]


def assert_model_training_results_equal(real_training_result, dummy_training_result):
    keys_to_check = ('title', 'type', 'model', 'framework', 'training_epochs', 'training_batch_size',
                     'training_final_loss')

    for key in keys_to_check:
        assert real_training_result[key] == dummy_training_result[key]


@pytest.fixture
def keys():
    private_key = os.environ.get("PRIVATE_KEY")
    env = os.environ.get("ENV")
    template_project_id = TEMPLATE_PROJECT_STAGING_ID if env == "STAGING" else TEMPLATE_PROJECT_DEV_ID

    if env == "STAGING":
        cord_domain = 'https://staging.api.cord.tech'
        template_project_feature_hashes = TEMPLATE_PROJECT_STAGING_FEATURE_HASHES
        template_project_dataset_hash = TEMPLATE_PROJECT_STAGING_DATASET_HASH

    else:
        if env == "DEV":
            cord_domain = 'https://dev.api.cord.tech'
        else:
            cord_domain = 'http://127.0.0.1:8000'
      
        template_project_feature_hashes = TEMPLATE_PROJECT_DEV_FEATURE_HASHES
        template_project_dataset_hash = TEMPLATE_PROJECT_DEV_DATASET_HASH

    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    api_key = user_client.get_project_api_keys(template_project_id)[0]
    template_client_project = CordClient.initialise(template_project_id, api_key.api_key, domain=cord_domain)

    return PytestKeys(private_key, cord_domain, template_client_project,
                      template_project_feature_hashes, template_project_dataset_hash, template_project_id)


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


def get_label_hash(client: CordClientProject):
    project = client.get_project()
    label_rows = project["label_rows"][0]
    return label_rows["label_hash"]


def get_data_hash(client: CordClientProject):
    project = client.get_project()
    label_rows = project["label_rows"][0]
    return label_rows["data_hash"]


def test_create_project_with_no_datasets(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)

    project_hash = user_client.create_project("test project", [], "")

    assert isinstance(project_hash, str)


def test_create_project_api_key(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    project_hash = user_client.create_project("test project with api key", [], "")

    api_key = user_client.create_project_api_key(project_hash, "test api key", [scope for scope in APIKeyScopes])

    assert isinstance(api_key, str)


def test_get_project_api_keys(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
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
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    dataset_title = "test dataset"
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    dataset = user_client.create_dataset(dataset_title, DatasetType.CORD_STORAGE)

    assert isinstance(dataset, dict)
    assert dataset["title"] == dataset_title
    assert dataset["type"] == DatasetType.CORD_STORAGE
    assert isinstance(dataset["dataset_hash"], str)


def test_create_dataset_api_key(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    dataset = user_client.create_dataset("test dataset", DatasetType.CORD_STORAGE)
    dataset_hash = dataset["dataset_hash"]

    api_key = user_client.create_dataset_api_key(dataset_hash, "test api key", [scope for scope in DatasetScope])

    assert isinstance(api_key, DatasetAPIKey)
    assert isinstance(api_key.api_key, str)


def test_get_dataset_api_keys(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    dataset = user_client.create_dataset("test dataset", DatasetType.CORD_STORAGE)
    dataset_hash = dataset["dataset_hash"]
    api_key_1 = user_client.create_dataset_api_key(dataset_hash, "test api key", [DatasetScope.READ])
    api_key_2 = user_client.create_dataset_api_key(dataset_hash, "test api key", [DatasetScope.WRITE])

    all_api_keys = user_client.get_dataset_api_keys(dataset_hash)

    assert api_key_1 in all_api_keys
    assert api_key_2 in all_api_keys


def test_add_datasets_to_project(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    dataset_1 = user_client.create_dataset("test dataset1", DatasetType.CORD_STORAGE)
    dataset_2 = user_client.create_dataset("test dataset1", DatasetType.AWS)
    dataset_1_hash = dataset_1["dataset_hash"]
    dataset_2_hash = dataset_2["dataset_hash"]
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_domain)

    result = client.add_datasets([dataset_1_hash, dataset_2_hash])

    assert result


def test_remove_datasets_datasets_from_project(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    dataset_1 = user_client.create_dataset("test dataset1", DatasetType.CORD_STORAGE)
    dataset_2 = user_client.create_dataset("test dataset1", DatasetType.AWS)
    dataset_1_hash = dataset_1["dataset_hash"]
    dataset_2_hash = dataset_2["dataset_hash"]
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_domain)
    client.add_datasets([dataset_1_hash, dataset_2_hash])

    result = client.remove_datasets([dataset_1_hash])

    assert result


def test_add_users_to_project(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_domain)

    users = client.add_users(["testuser1@cord.tech", "testuser2@cord.tech"], ProjectUserRole.ANNOTATOR)

    assert ProjectUser("testuser1@cord.tech", ProjectUserRole.ANNOTATOR, project_hash) in users
    assert ProjectUser("testuser2@cord.tech", ProjectUserRole.ANNOTATOR, project_hash) in users


def test_show_empty_project_ontology(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_domain)

    ontology = client.get_project_ontology()

    assert ontology.to_dict() == Ontology().to_dict()


@patch('cord.project_ontology.ontology.generate_feature_node_hash')
def test_update_existing_ontology(generate_feature_node_hash, keys):
    generate_feature_node_hash.return_value = get_dummy_feature_node_hash()
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])
    client = CordClient.initialise(project_hash, project_api_key, cord_domain)

    client.add_object("box", ObjectShape.BOUNDING_BOX)
    client.add_object("polygon", ObjectShape.POLYGON)
    client.add_classification("checklist", ClassificationType.CHECKLIST, True, ["a", "b", "c"])
    client.add_classification("radio", ClassificationType.RADIO, False, ["d", "e", "f"])
    client.add_classification("text", ClassificationType.TEXT, False)

    ontology = client.get_project_ontology()
    expected_ontology = get_expected_project_ontology()

    assert ontology.to_dict() == expected_ontology.to_dict()


def test_get_label_row(keys):
    client = keys.template_client_project
    label_hash = get_label_hash(client)

    label_row = client.get_label_row(label_hash)

    assert label_row["data_units"].keys()


def test_save_label_row(keys):
    client = keys.template_client_project
    label_hash = get_label_hash(client)
    label_row = client.get_label_row(label_hash)
    label_row_dict = label_utilities.construct_answer_dictionaries(label_row)

    save_result = client.save_label_row(label_hash, label_row_dict)

    assert save_result


def test_create_label_row(keys):
    private_key = keys.private_key
    cord_domain = keys.cord_domain
    template_project_dataset_hash = keys.template_project_dataset_hash
    user_client = CordUserClient.create_with_ssh_private_key(private_key, domain=cord_domain)
    project_hash = user_client.create_project("test project with dataset", [], "")
    project_api_key = user_client.create_project_api_key(project_hash, "api key", [scope for scope in APIKeyScopes])

    client = CordClient.initialise(project_hash, project_api_key, cord_domain)
    client.add_datasets([template_project_dataset_hash])
    data_hash = get_data_hash(client)

    label_row = client.create_label_row(data_hash)

    assert isinstance(label_row['label_hash'], str)
    assert isinstance(label_row['dataset_hash'], str)
    data_units = label_row['data_units'][data_hash]
    assert isinstance(data_units['data_hash'], str)
    assert isinstance(data_units['data_link'], str)

    assert_empty_labels_rows_equal(label_row, EMPTY_LABEL_ROW)


def test_create_model_row(keys):
    client = keys.template_client_project
    feature_hashes = keys.template_project_feature_hashes

    model_hash = client.create_model_row(title='Test model',
                                         description='A test model',
                                         features=feature_hashes,
                                         model=FASTER_RCNN)
    delete_result = client.model_delete(model_hash)

    assert isinstance(model_hash, str)
    assert delete_result


def test_get_label_logs(keys):
    client = keys.template_client_project
    data_hash = get_data_hash(client)

    label_logs = client.get_label_logs(data_hash=data_hash)

    assert len(label_logs) > 0
    for label_log in label_logs:
        assert isinstance(label_log, LabelLog)


def test_model_train(keys):
    client = keys.template_client_project
    client._config.write_timeout = 600
    feature_hashes = keys.template_project_feature_hashes
    label_hash = get_label_hash(client)
    project_hash = keys.template_project_hash
    model_hash = client.create_model_row(title='Test model ' + str(datetime.utcnow()),
                                         description='A test model',
                                         features=feature_hashes,
                                         model=FASTER_RCNN)

    model_train = client.model_train(model_hash, [label_hash], TRAINING_EPOCH_SIZE, TRAINING_BATCH_SIZE,
                                     faster_rcnn_R_101_FPN_3x, device="cpu")
    delete_result = client.model_delete(model_hash)

    model_training_result = model_train["response"][0]

    assert model_train["status"]
    assert_model_training_results_equal(model_training_result, DUMMY_MODEL_TRAINING_RESULT)
    assert isinstance(model_training_result["training_hash"], str)
    assert isinstance(model_training_result["training_config_link"], str)
    assert isinstance(model_training_result["training_names_link"], str)
    assert isinstance(model_training_result["training_weights_link"], str)
    assert isinstance(model_training_result["created_at"], str)
    assert isinstance(model_training_result["training_duration"], int)
    assert model_training_result["project_hash"] == project_hash
    assert model_training_result["model_hash"] == model_hash
    assert delete_result


# todo
def test_model_inference(keys):
    pass
