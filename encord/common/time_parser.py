from datetime import datetime

from dateutil import parser


def parse_datetime(time_string: str) -> datetime:
    """
    Parsing datetime strings in the most compatible yet performant way.

    Our labels can contain timestamps in different formats, but applying dateutil.parse straight away is expensive
    as it is very smart and tries to guess the time format.

    So instead we're applying parsers with known formats, starting from the formats most likely to occur,
    and falling back to the most complicated logic only in case of all other attempt have failed.
    """
    try:
        return datetime.strptime(time_string, "%a, %d %b %Y %H:%M:%S %Z")
    except Exception:
        pass

    try:
        return parser.isoparse(time_string)
    except Exception:
        pass

    return parser.parse(time_string)
