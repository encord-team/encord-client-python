from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class Page(Generic[T]):
    results: List[T]
    next_page_token: Optional[str]


class Timer:
    name: str
