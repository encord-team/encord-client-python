from __future__ import annotations

from enum import Enum
from typing import Optional, cast


class StringEnum(Enum):
    """
    Use this enum class if you need the helper that creates the enum instance from a string.
    """

    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, value: str) -> Optional[StringEnum]:
        # pylint: disable-next=no-member
        return cast(StringEnum, cls._value2member_map_.get(value))
