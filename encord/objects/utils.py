from __future__ import annotations

import base64
import re
import uuid
from typing import Any, List, Optional, TypeVar


def _decode_nested_uid(nested_uid: list) -> str:
    return ".".join([str(uid) for uid in nested_uid])


def short_uuid_str() -> str:
    """This is being used as a condensed uuid."""
    return base64.b64encode(uuid.uuid4().bytes[:6]).decode("utf-8")


def _lower_snake_case(s: str):
    return s.lower().replace(" ", "_")


def check_type(obj: object, type_: Any) -> None:
    if not does_type_match(obj, type_):
        raise TypeError(f"Expected {type_}, got {type(obj)}")


def does_type_match(obj: object, type_: Any) -> bool:
    if type_ is None:
        return True
    if not isinstance(obj, type_):
        return False
    return True


T = TypeVar("T")


def filter_by_type(objects: List[object], type_: Optional[T]) -> List[T]:
    return [object_ for object_ in objects if does_type_match(object_, type_)]


def is_valid_email(email: str) -> bool:
    """
    Validate that an email is a valid one
    """
    regex = r"[^@]+@[^@]+\.[^@]+"
    return bool(re.match(regex, email))


def check_email(email: str) -> None:
    if not is_valid_email(email):
        raise ValueError("Invalid email address")
