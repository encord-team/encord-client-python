"""Unit tests for the dataset class"""


from datetime import datetime
from dateutil import parser

from encord.constants.enums import DataType
from encord.orm.dataset import Dataset, StorageLocation

DATASET_JSON = {
    "title": "CVAT imported baking dataset",
    "description": "Suiting description",
    "dataset_type": "CORD_STORAGE",
    "data_rows": [
        {
            "data_hash": "87fb7247-794b-4dad-b378-4e574723c05e",
            "data_title": "image-group-12dca",
            "created_at": "2022-01-05 18:51:05",
            "data_type": "IMG_GROUP",
        }
    ],
}


def test_dataset_conversions():
    dataset = Dataset.from_dict(DATASET_JSON)

    assert dataset == DATASET_JSON


def test_dataset_fields():
    dataset = Dataset.from_dict(DATASET_JSON)

    assert dataset.title == DATASET_JSON["title"]
    assert dataset.description == DATASET_JSON["description"]
    assert dataset.storage_location == StorageLocation.CORD_STORAGE

    data_row = dataset.data_rows[0]
    data_row_json = DATASET_JSON["data_rows"][0]

    assert data_row.uid == data_row_json["data_hash"]
    assert data_row.title == data_row_json["data_title"]
    assert data_row.created_at == parser.parse(data_row_json["created_at"])
    assert data_row.data_type == DataType.from_upper_case_string(data_row_json["data_type"])


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
