from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T", bound="BaseDTOInterface")


class BaseDTOInterface(ABC):
    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass
