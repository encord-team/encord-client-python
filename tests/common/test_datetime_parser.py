from datetime import datetime, timedelta, timezone

from encord.common.constants import DATETIME_LONG_STRING_FORMAT
from encord.common.time_parser import parse_datetime


def test_can_parse_iso_timestamp() -> None:
    expected_datetime = datetime.now()

    datetime_as_iso = expected_datetime.isoformat()
    parsed_datetime = parse_datetime(datetime_as_iso)

    assert parsed_datetime == expected_datetime


def test_can_parse_encord_time_format() -> None:
    original_datetime = datetime.now()

    datetime_as_encord_string = original_datetime.strftime(DATETIME_LONG_STRING_FORMAT)
    parsed_datetime = parse_datetime(datetime_as_encord_string)

    # Short string format doesn't include milliseconds, so dropping them
    expected_datetime = original_datetime.replace(microsecond=0)
    assert parsed_datetime == expected_datetime


def test_can_parse_encord_time_from() -> None:
    original_datetime = "Thu Jan 11 2024 12:09:51 GMT+0600 (Bangladesh Standard Time)"
    parsed_datetime = parse_datetime(original_datetime)

    expected_datetime = datetime(2024, 1, 11, 12, 9, 51, tzinfo=timezone(timedelta(hours=-6)))
    assert parsed_datetime == expected_datetime
