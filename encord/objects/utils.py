from __future__ import annotations

import base64
import re
import uuid
from typing import Any, Iterable, List, Optional, Type, TypeVar, cast


def _decode_nested_uid(nested_uid: list) -> str:
    return ".".join([str(uid) for uid in nested_uid])


def short_uuid_str() -> str:
    """This is being used as a condensed uuid."""
    return base64.b64encode(uuid.uuid4().bytes[:6]).decode("utf-8")


def _lower_snake_case(s: str):
    return s.lower().replace(" ", "_")


def _snake_to_camel(snake_case_str: str) -> str:
    camel = re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), snake_case_str.title())
    return re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)


def check_type(obj: Any, type_: Optional[Type[Any]]) -> None:
    if not does_type_match(obj, type_):
        raise TypeError(f"Expected {type_}, got {type(obj)}")


def does_type_match(obj: Any, type_: Optional[Type[Any]]) -> bool:
    if type_ is None:
        return True
    if not isinstance(obj, type_):
        return False
    return True


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
