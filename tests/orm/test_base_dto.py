import uuid
from datetime import datetime, timezone
from typing import List

import pytest
from pydantic import ValidationError

from encord.common.constants import DATETIME_LONG_STRING_FORMAT, DATETIME_STRING_FORMAT
from encord.exceptions import EncordException
from encord.orm.base_dto import BaseDTO, dto_validator
from encord.orm.dataset import DatasetDataLongPolling, LongPollingStatus


class TestModel(BaseDTO):
    text_value: str
    number_value: int
    datetime_value: datetime


class TestModelWithLists(BaseDTO):
    text_values: List[str]
    number_values: List[int]
    datetime_values: List[datetime]


def test_basic_model_with_deserialization():
    time_value = datetime.now()
    data_dict = {
        "text_value": "abc",
        "number_value": 22,
        "datetime_value": time_value.strftime(DATETIME_LONG_STRING_FORMAT),
    }

    model = TestModel.from_dict(data_dict)

    assert model.text_value == "abc"
    assert model.number_value == 22
    assert model.datetime_value == time_value.replace(microsecond=0)


def test_basic_model_with_encord_time_deserialization():
    time_value = datetime.now()
    data_dict = {"text_value": "abc", "number_value": 22, "datetime_value": str(time_value)}

    model = TestModel.from_dict(data_dict)

    assert model.text_value == "abc"
    assert model.number_value == 22
    assert model.datetime_value == time_value


def test_basic_model_with_value_containers_deserialization():
    data_dict = {
        "text_values": ["abc", "def"],
        "number_values": [22, 33],
        "datetime_values": [
            str(datetime(year=2024, month=2, day=1, tzinfo=timezone.utc)),
            str(datetime(year=2024, month=2, day=1, tzinfo=timezone.utc)),
        ],
    }
    model = TestModelWithLists.from_dict(data_dict)
    assert model.text_values == ["abc", "def"]
    assert model.number_values == [22, 33]
    assert model.datetime_values == [
        datetime(year=2024, month=2, day=1, tzinfo=timezone.utc),
        datetime(year=2024, month=2, day=1, tzinfo=timezone.utc),
    ]


def test_complex_model_deserialization():
    backing_item_uuid = uuid.uuid4()
    data_dict = {
        "status": "PENDING",
        "errors": ["error one", "error two"],
        "units_pending_count": 5,
        "units_done_count": 5,
        "units_error_count": 2,
        "data_hashes_with_titles": [
            {"data_hash": "abc", "title": "dummy title", "backing_item_uuid": str(backing_item_uuid)}
        ],
        "data_unit_errors": [],
    }

    model = DatasetDataLongPolling.from_dict(data_dict)
    assert model.status == LongPollingStatus.PENDING
    assert model.errors == ["error one", "error two"]
    assert model.data_hashes_with_titles[0].data_hash == "abc"
    assert model.data_hashes_with_titles[0].title == "dummy title"
    assert model.data_hashes_with_titles[0].backing_item_uuid == backing_item_uuid


class TestModelWithValidator(TestModel):
    @dto_validator(mode="before")
    def validate(cls, values):
        number: int = values.get("number_value")
        assert number > 0
        return values

    @dto_validator(mode="after")
    def validate_after(cls, instance: "TestModelWithValidator"):
        assert instance.number_value > 0
        return instance


def test_dto_validator():
    time_value = datetime.now()
    data_dict = {
        "text_value": "abc",
        "number_value": 22,
        "datetime_value": time_value.strftime(DATETIME_LONG_STRING_FORMAT),
    }
    valid_case = TestModelWithValidator.from_dict(data_dict)
    assert valid_case.number_value == 22

    invalid_data = data_dict
    invalid_data["number_value"] = -10

    with pytest.raises(EncordException):
        TestModelWithValidator.from_dict(invalid_data)
