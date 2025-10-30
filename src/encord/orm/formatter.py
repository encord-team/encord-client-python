from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T", bound="Formatter")


class Formatter(ABC):
    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], json_dict: Dict[str, Any]) -> T:
        pass
