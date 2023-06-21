from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    results: List[T]
    next_page_token: Optional[str]
