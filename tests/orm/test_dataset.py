"""Unit tests for the dataset class"""

from datetime import datetime
from typing import Set

from encord.common.time_parser import parse_datetime
from encord.constants.enums import DataType
from encord.orm.dataset import Dataset, StorageLocation

DATASET_JSON = {
    "dataset_hash": "93a90f72-0da4-47d9-8ffe-b779a7d0b22a",
    "title": "CVAT imported baking dataset",
    "description": "Suiting description",
    "dataset_type": "CORD_STORAGE",
    "backing_folder_uuid": None,
    "data_rows": [
        {
            "data_hash": "87fb7247-794b-4dad-b378-4e574723c05e",
            "backing_item_uuid": None,
            "data_title": "image-group-12dca",
            "created_at": "2022-01-05 18:51:05",
            "last_edited_at": "2022-01-05 19:23:56",
            "width": 1280,
            "height": 1430,
            "file_link": "'cord-images-dev/cNUDa8SPDuaTs0hk00tDadsrtDJ3/37ec818c-fbbf-4fde-8cf2-5766d8295bdc",
            "file_size": 3560366.0,
            "file_type": "image/png",
            "data_type": "IMG_GROUP",
            "client_metadata": {"key": "value"},
            "storage_location": StorageLocation.CORD_STORAGE.value,
            "is_optimised_image_group": None,
            "frames_per_second": None,
            "duration": None,
            "_querier": None,
            "_dirty_fields": [],
            "images_data": None,
            "signed_url": None,
        }
    ],
}


def test_dataset_conversions():
    dataset = Dataset.from_dict(DATASET_JSON)

    assert dataset == DATASET_JSON


def test_dataset_fields():
    dataset = Dataset.from_dict(DATASET_JSON)

    assert dataset.dataset_hash == DATASET_JSON["dataset_hash"]
    assert dataset.title == DATASET_JSON["title"]
    assert dataset.description == DATASET_JSON["description"]
    assert dataset.storage_location == StorageLocation.CORD_STORAGE

    data_row = dataset.data_rows[0]
    data_row_json = DATASET_JSON["data_rows"][0]

    assert data_row.uid == data_row_json["data_hash"]
    assert data_row.title == data_row_json["data_title"]
    assert data_row.created_at == parse_datetime(data_row_json["created_at"])
    assert data_row.data_type == DataType.from_upper_case_string(data_row_json["data_type"])
    assert data_row.client_metadata == data_row_json["client_metadata"]
    assert data_row.last_edited_at == parse_datetime(data_row_json["last_edited_at"])
    assert data_row.width == data_row_json["width"]
    assert data_row.height == data_row_json["height"]
    assert data_row.file_link == data_row_json["file_link"]
    assert data_row.file_size == data_row_json["file_size"]
    assert data_row.file_type == data_row_json["file_type"]
    assert data_row.storage_location == data_row_json["storage_location"]
    assert data_row.frames_per_second == data_row_json["frames_per_second"]
    assert data_row.duration == data_row_json["duration"]


def test_dataset_setters_and_getters():
    dataset = Dataset.from_dict(DATASET_JSON)
    title = "New title"
    description = "New description"
    storage_location = StorageLocation.CORD_STORAGE

    dataset.title = title
    dataset.description = description
    dataset.storage_location = storage_location

    assert dataset.title == title
    assert dataset.description == description
    assert dataset.storage_location == storage_location

    uid = "123456"
    data_row_title = "Datarow title"
    created_at = datetime(2022, 1, 12, 15, 25, 54)
    data_type = DataType.VIDEO

    data_row = dataset.data_rows[0]
    data_row.uid = uid
    data_row.title = data_row_title
    data_row.created_at = created_at
    data_row.data_type = data_type

    assert data_row.uid == uid
    assert data_row.title == data_row_title
    assert data_row.created_at == created_at
    assert data_row.data_type == data_type


def test_dataset_backwards_compatibility():
    dataset = Dataset.from_dict(DATASET_JSON)

    assert "title" in dataset

    # all the following ones are available
    dataset.items()
    dataset.keys()
    dataset.values()
    assert dataset["title"] == DATASET_JSON["title"]
    assert dataset["description"] == DATASET_JSON["description"]
    assert dataset["dataset_type"] == DATASET_JSON["dataset_type"]
    assert dataset["data_rows"] == DATASET_JSON["data_rows"]


def test_storage_location_default():
    assert StorageLocation(0) == StorageLocation.CORD_STORAGE
    assert StorageLocation(100) == StorageLocation.NEW_STORAGE


def test_storage_location_to_str() -> None:
    unique_representations: set[StorageLocation] = set()

    for location in StorageLocation:
        string_representation = StorageLocation.get_str(location)
        location_from_string = StorageLocation.from_str(string_representation)

        unique_representations.add(location)

        assert isinstance(string_representation, str)
        assert location == location_from_string

    assert len(unique_representations) == len(StorageLocation)
