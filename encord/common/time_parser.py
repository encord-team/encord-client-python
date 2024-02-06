import contextlib
from datetime import datetime

from dateutil import parser

from encord.common.constants import DATETIME_LONG_STRING_FORMAT


def parse_datetime(time_string: str) -> datetime:
    """
    Parsing datetime strings in the most compatible yet performant way.

    Our labels can contain timestamps in different formats, but applying dateutil.parse straight away is expensive
    as it is very smart and tries to guess the time format.

    So instead we're applying parsers with known formats, starting from the formats most likely to occur,
    and falling back to the most complicated logic only in case of all other attempt have failed.
    """
    with contextlib.suppress(Exception):
        return datetime.strptime(time_string, DATETIME_LONG_STRING_FORMAT)
    with contextlib.suppress(Exception):
        return parser.isoparse(time_string)
    with contextlib.suppress(Exception):
        return parser.parse(time_string)

    # As a last resort, employ fuzzy parsing, which is most expensive,
    # but parses the most obscure timestamp formats
    return parser.parse(time_string, fuzzy=True)
