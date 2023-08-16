from __future__ import annotations

import base64
import re
import uuid
from typing import Any, Iterable, List, Optional, Type, TypeVar, cast


def short_uuid_str() -> str:
    """This is being used as a condensed uuid."""
    return base64.b64encode(uuid.uuid4().bytes[:6]).decode("utf-8")


def _lower_snake_case(s: str):
    return s.lower().replace(" ", "_")


def check_type(obj: Any, type_: Optional[Type[Any]]) -> None:
    if not does_type_match(obj, type_):
        raise TypeError(f"Expected {type_}, got {type(obj)}")


def does_type_match(obj: Any, type_: Optional[Type[Any]]) -> bool:
    return True if type_ is None else isinstance(obj, type_)


T = TypeVar("T")


def checked_cast(obj: Any, type_: Optional[Type[T]]) -> T:
    check_type(obj, type_)
    return cast(T, obj)


def filter_by_type(objects: Iterable[Any], type_: Optional[Type[T]]) -> List[T]:
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
