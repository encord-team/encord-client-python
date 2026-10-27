from typing import Generic, List, Optional, TypeVar

from encord.orm.base_dto import GenericBaseDTO

T = TypeVar("T")


class Page(GenericBaseDTO, Generic[T]):
    results: List[T]
    next_page_token: Optional[str] = None


class ItemsPage(GenericBaseDTO, Generic[T]):
    """A page from an endpoint that returns its results under ``items`` rather than ``results``."""

    items: List[T]
    next_page_token: Optional[str] = None
