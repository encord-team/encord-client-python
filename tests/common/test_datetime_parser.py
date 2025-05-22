from datetime import datetime, timedelta, timezone

import pytest

from encord.common.constants import DATETIME_LONG_STRING_FORMAT
from encord.common.time_parser import format_datetime_to_long_string, parse_datetime


@pytest.mark.parametrize(
    "timezone_offset",
    [-12, -7, -3, 0, 2, 5, 11],
)
def test_parse_datetime_timezone_aware_iso_string(timezone_offset) -> None:
    tz = timezone(timedelta(hours=timezone_offset))
    expected_datetime = datetime.now(tz=tz)

    datetime_as_iso_string = expected_datetime.isoformat()
    parsed_datetime = parse_datetime(datetime_as_iso_string)

    assert parsed_datetime == expected_datetime


def test_parse_datetime_timezone_naive_iso_string() -> None:
    expected_datetime = datetime.now()

    datetime_as_iso_string = expected_datetime.isoformat()
    parsed_datetime = parse_datetime(datetime_as_iso_string)

    assert parsed_datetime == expected_datetime.replace(tzinfo=timezone.utc)


@pytest.mark.parametrize("timezone_name", ["", "UTC", "GMT"])
def test_parse_datetime_encord_string(timezone_name: str) -> None:
    expected_datetime = datetime.now()

    datetime_as_encord_string = expected_datetime.strftime(DATETIME_LONG_STRING_FORMAT) + f"{timezone_name}"
    parsed_datetime = parse_datetime(datetime_as_encord_string)

    # Encord string format doesn't include milliseconds, so dropping them
    assert parsed_datetime == expected_datetime.replace(microsecond=0, tzinfo=timezone.utc)


def test_parse_datetime_custom_string() -> None:
    expected_datetime_str = "Thu Jan 11 2024 12:09:51 GMT+0600 (Bangladesh Standard Time)"
    expected_datetime = datetime(2024, 1, 11, 12, 9, 51, tzinfo=timezone(timedelta(hours=-6)))

    parsed_datetime = parse_datetime(expected_datetime_str)

    assert parsed_datetime == expected_datetime


@pytest.mark.parametrize(
    "timezone_offset",
    [-12, -7, -3, 0, 2, 5, 11],
)
def test_format_datetime_to_long_string(timezone_offset: int) -> None:
    tz = timezone(timedelta(hours=timezone_offset))
    expected_datetime = datetime.now(tz=tz)

    expected_datetime_str = format_datetime_to_long_string(expected_datetime)
    parsed_datetime = parse_datetime(expected_datetime_str)

    # Encord string format doesn't include milliseconds, so dropping them
    assert parsed_datetime == expected_datetime.replace(microsecond=0)
