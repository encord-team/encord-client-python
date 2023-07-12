from __future__ import annotations

from enum import Enum
from typing import Optional, Type, TypeVar, cast

T = TypeVar("T", bound="StringEnum")


class StringEnum(Enum):
    """
    Use this enum class if you need the helper that creates the enum instance from a string.
    """

    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls: Type[T], value: str) -> Optional[T]:
        # pylint: disable-next=no-member
        return cast(T, cls._value2member_map_.get(value))
