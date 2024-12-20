from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T", bound="Formatter")


class Formatter(ABC):
    @classmethod
    @abstractmethod
    def from_dict(cls: type[T], json_dict: dict[str, Any]) -> T:
        pass
