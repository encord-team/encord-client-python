import uuid
from datetime import datetime, timezone
from typing import List

import pytest

from encord.common.time_parser import format_datetime_to_long_string
from encord.exceptions import EncordException
from encord.orm.base_dto import BaseDTO, BaseDTOWithExtra, dto_validator
from encord.orm.dataset import DatasetDataLongPolling, LongPollingStatus


class TestModel(BaseDTO):
    text_value: str
    number_value: int
    datetime_value: datetime


class TestModelWithLists(BaseDTO):
    text_values: List[str]
    number_values: List[int]
    datetime_values: List[datetime]


class TestModelWithExtra(BaseDTOWithExtra):
    text_value: str


def test_deserialize_model_with_extra():
    datetime_value = datetime.now()
    data_dict = {
        "text_value": "abc",
        "int_value": 22,
        "float_value": 22.22,
        "datetime_value": format_datetime_to_long_string(datetime_value),
    }

    model = TestModelWithExtra.from_dict(data_dict)

    assert model.text_value == "abc"
    assert model.get_extra("int_value") == 22
    assert model.get_extra("float_value") == 22.22
    assert isinstance(model.get_extra("datetime_value"), str)


def test_basic_model_with_deserialization():
    datetime_value = datetime.now()
    data_dict = {
        "text_value": "abc",
        "number_value": 22,
        "datetime_value": format_datetime_to_long_string(datetime_value),
    }

    model = TestModel.from_dict(data_dict)

    assert model.text_value == "abc"
    assert model.number_value == 22
    assert model.datetime_value == datetime_value.replace(microsecond=0, tzinfo=timezone.utc)


def test_basic_model_with_naive_iso_datetime_deserialization():
    datetime_value = datetime.now()
    data_dict = {"text_value": "abc", "number_value": 22, "datetime_value": str(datetime_value)}

    model = TestModel.from_dict(data_dict)

    assert model.text_value == "abc"
    assert model.number_value == 22
    assert model.datetime_value == datetime_value.replace(tzinfo=timezone.utc)


def test_basic_model_with_value_containers_deserialization():
    data_dict = {
        "text_values": ["abc", "def"],
        "number_values": [22, 33],
        "datetime_values": [
            str(datetime(year=2024, month=2, day=1, tzinfo=timezone.utc)),
            str(datetime(year=2024, month=2, day=2, tzinfo=timezone.utc)),
        ],
    }
    model = TestModelWithLists.from_dict(data_dict)
    assert model.text_values == ["abc", "def"]
    assert model.number_values == [22, 33]
    assert model.datetime_values == [
        datetime(year=2024, month=2, day=1, tzinfo=timezone.utc),
        datetime(year=2024, month=2, day=2, tzinfo=timezone.utc),
    ]


def test_complex_model_deserialization():
    backing_item_uuid = uuid.uuid4()
    data_dict = {
        "status": "PENDING",
        "errors": ["error one", "error two"],
        "units_pending_count": 5,
        "units_done_count": 5,
        "units_error_count": 2,
        "units_cancelled_count": 0,
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
        assert instance.text_value == "abc"
        instance.text_value += "-postfix"
        return instance


def test_dto_validator():
    datetime_value = datetime.now()
    data_dict = {
        "text_value": "abc",
        "number_value": 22,
        "datetime_value": format_datetime_to_long_string(datetime_value),
    }
    valid_case = TestModelWithValidator.from_dict(data_dict)
    assert valid_case.number_value == 22
    assert valid_case.text_value == f"{data_dict['text_value']}-postfix"
    assert valid_case.datetime_value == datetime_value.replace(microsecond=0, tzinfo=timezone.utc)

    invalid_data = data_dict
    invalid_data["number_value"] = -10

    with pytest.raises(EncordException):
        TestModelWithValidator.from_dict(invalid_data)
