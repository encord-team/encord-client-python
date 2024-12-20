from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T", bound="BaseDTOInterface")


class BaseDTOInterface(ABC):
    @classmethod
    @abstractmethod
    def from_dict(cls: type[T], d: dict[str, Any]) -> T:
        pass

    @abstractmethod
    def to_dict(self, by_alias=True, exclude_none=True) -> dict[str, Any]:
        pass
