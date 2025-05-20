import contextlib
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional, Union

from dateutil import parser

from encord.common.constants import DATETIME_LONG_STRING_FORMAT


# Cache: major performance win for large classification ranges
@lru_cache(maxsize=8192)
def parse_datetime(time_string: str) -> datetime:
    """Parsing datetime strings to timezone-aware datetime objects efficiently.

    If no timezone information is present in the string, UTC is assumed.

    Our labels can contain timestamps in different formats, but applying dateutil.parse straight away is expensive
    as it is very smart and tries to guess the time format.

    So instead we're applying parsers with known formats, starting from the formats most likely to occur,
    and falling back to the most complicated logic only in case of all other attempts have failed.

    Args:
        time_string: A string containing a datetime in various possible formats.

    Returns:
        A timezone-aware datetime object (UTC if no timezone was specified).
    """
    parsed_datetime: Optional[datetime] = None
    if time_string.endswith("UTC") or time_string.endswith("GMT"):
        # Parse datetimes with DATETIME_LONG_STRING_FORMAT (Thu, 01 May 2025 13:53:59 GMT)
        # Note: As datetime.strptime() without %z returns a naive datetime object we enforce UTC timezone here.
        with contextlib.suppress(Exception):
            parsed_datetime = datetime.strptime(time_string, DATETIME_LONG_STRING_FORMAT).replace(tzinfo=timezone.utc)
    if parsed_datetime is None:
        # Parse datetimes with ISO 8601 format (2025-05-01T23:53:59+10:00)
        with contextlib.suppress(Exception):
            parsed_datetime = parser.isoparse(time_string)
    if parsed_datetime is None:
        # Parse datetimes with a common unspecified format
        with contextlib.suppress(Exception):
            parsed_datetime = parser.parse(time_string)
    if parsed_datetime is None:
        # As a last resort, use fuzzy parsing, which is most expensive, but parses the most obscure timestamp formats
        parsed_datetime = parser.parse(time_string, fuzzy=True)

    # If no timezone information is present in the string, UTC is assumed.
    if parsed_datetime.tzinfo is None:
        parsed_datetime = parsed_datetime.replace(tzinfo=timezone.utc)
    return parsed_datetime


def parse_datetime_optional(_datetime: Optional[Union[str, datetime]]) -> Optional[datetime]:
    if _datetime is None:
        return None
    elif isinstance(_datetime, datetime):
        return _datetime
    elif isinstance(_datetime, str):
        return parse_datetime(_datetime)
    else:
        raise ValueError(f"parse_datetime_optional {type(_datetime)=} not supported")
