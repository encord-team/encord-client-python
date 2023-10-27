"""Unit tests for the dataset class"""
import uuid

from encord.orm.dataset import CreateDatasetResponse, StorageLocation

DATASET_RESPONSE_JSON = {
    "title": "CVAT imported baking dataset",
    "type": 0,
    "dataset_hash": "460505dd-89ea-485a-b4ea-417558a26889",
    "backing_folder_uuid": "434df998-3aac-423d-bc29-1af33040e583",
    "user_hash": "yiA5JxmLEGSoEcJAuxr3AJdDDXE2",
}


def test_create_dataset_response_conversions():
    create_dataset_response = CreateDatasetResponse.from_dict(DATASET_RESPONSE_JSON)

    assert isinstance(create_dataset_response["backing_folder_uuid"], uuid.UUID)
    create_dataset_response["backing_folder_uuid"] = str(create_dataset_response["backing_folder_uuid"])

    assert create_dataset_response == DATASET_RESPONSE_JSON


def test_create_dataset_response_fields():
    create_dataset_response = CreateDatasetResponse.from_dict(DATASET_RESPONSE_JSON)

    assert create_dataset_response.title == DATASET_RESPONSE_JSON["title"]
    assert create_dataset_response.storage_location == StorageLocation.CORD_STORAGE
    assert create_dataset_response.dataset_hash == DATASET_RESPONSE_JSON["dataset_hash"]
    assert create_dataset_response.user_hash == DATASET_RESPONSE_JSON["user_hash"]


def test_create_dataset_response_setters_and_getters():
    create_dataset_response = CreateDatasetResponse.from_dict(DATASET_RESPONSE_JSON)
    title = "New title"
    storage_location = StorageLocation.AWS
    dataset_hash = "123456"
    user_hash = "abcdef"

    create_dataset_response.title = title
    create_dataset_response.storage_location = storage_location
    create_dataset_response.dataset_hash = dataset_hash
    create_dataset_response.user_hash = user_hash

    assert create_dataset_response.title == title
    assert create_dataset_response.storage_location == storage_location
    assert create_dataset_response.dataset_hash == dataset_hash
    assert create_dataset_response.user_hash == user_hash


def test_create_dataset_response_backwards_compatibility():
    create_dataset_response = CreateDatasetResponse.from_dict(DATASET_RESPONSE_JSON)

    assert "title" in create_dataset_response

    # all the following ones are available
    create_dataset_response.items()
    create_dataset_response.keys()
    create_dataset_response.values()

    assert create_dataset_response["title"] == DATASET_RESPONSE_JSON["title"]
    assert create_dataset_response["type"] == DATASET_RESPONSE_JSON["type"]
    assert create_dataset_response["dataset_hash"] == DATASET_RESPONSE_JSON["dataset_hash"]
    assert create_dataset_response["user_hash"] == DATASET_RESPONSE_JSON["user_hash"]
