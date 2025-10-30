from __future__ import annotations

import re
from typing import List, Optional, TypeVar, Union
from uuid import UUID


def snake_to_camel(snake_case_str: str) -> str:
    camel = re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), snake_case_str.title())
    return re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)


T = TypeVar("T")


def ensure_list(v: Union[List[T], T, None]) -> Optional[List[T]]:
    if v is None or isinstance(v, list):
        return v
    return [v]


def ensure_uuid_list(value: Union[List[UUID], List[str], UUID, str, None]) -> Optional[List[UUID]]:
    vs = ensure_list(value)
    if vs is None:
        return None

    results: List[UUID] = []
    for v in vs:
        if isinstance(v, UUID):
            results.append(v)
        elif isinstance(v, str):
            results.append(UUID(v))
        else:
            raise AssertionError(f"Can't convert {type(v)} to UUID")

    return results


def validate_user_agent_suffix(user_agent_suffix: str) -> str:
    """
    Validate a User-Agent string according to RFC 9110, excluding comments.
    Returns it whitespace trimmed
    Args:
        user_agent_suffix: The User-Agent string to validate

    Returns:
        The validated User-Agent string

    Raises:
        ValueError: If the User-Agent string is invalid
    """
    user_agent = user_agent_suffix.strip()
    # Define regex components
    tchar = r"[-!#$%&'*+.^_`|~0-9A-Za-z]"
    token = f"{tchar}+"
    product = f"{token}(?:/{token})?"
    RWS = r"[ \t]+"

    # Complete User-Agent pattern (just products separated by whitespace)
    pattern = re.compile(f"^{product}(?:{RWS}{product})*$")

    if not pattern.match(user_agent):
        raise ValueError(f"Invalid User-Agent string: '{user_agent_suffix}'. ")

    return user_agent
