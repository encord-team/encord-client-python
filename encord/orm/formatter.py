from abc import ABC, abstractmethod
from typing import Dict


class Formatter(ABC):
    @classmethod
    @abstractmethod
    def from_dict(cls, json_dict: Dict):
        pass
