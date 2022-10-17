from abc import ABC, abstractmethod
from typing import Dict, List, Union


class Formatter(ABC):
    @classmethod
    @abstractmethod
    def from_dict(cls, json_dict: Union[Dict, List]):
        pass
