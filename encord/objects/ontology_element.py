from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    cast,
)

from encord.exceptions import OntologyError
from encord.objects.utils import check_type, checked_cast, does_type_match

if TYPE_CHECKING:
    from encord.objects.common import NestedID

OntologyElementT = TypeVar("OntologyElementT", bound="OntologyElement")
OntologyNestedElementT = TypeVar("OntologyNestedElementT", bound="OntologyNestedElement")


@dataclass
class OntologyElement(ABC):
    feature_node_hash: str

    @property
    def children(self) -> Sequence[OntologyElement]:
        return []

    @property
    @abstractmethod
    def title(self) -> str:
        raise NotImplementedError("This method is not implemented for this class")

    def get_child_by_hash(
        self,
        feature_node_hash: str,
        type_: Optional[Type[OntologyNestedElementT]] = None,
    ) -> OntologyNestedElementT:
        """
        Returns the first child node of this ontology tree node with the matching feature node hash. If there is
        more than one child with the same feature node hash in the ontology tree node, then the ontology would be in
        an invalid state. Throws if nothing is found or if the type is not matched.

        Args:
            feature_node_hash: the feature_node_hash of the child node to search for in the ontology.
            type_: The expected type of the item. If the found child does not match the type, an error will be thrown.
        """
        found_item = _get_element_by_hash(feature_node_hash, self.children)
        if found_item is None:
            raise OntologyError("Item not found.")
        check_type(found_item, type_)
        return found_item

    def get_children_by_title(
        self,
        title: str,
        type_: Optional[Type[OntologyNestedElementT]] = None,
    ) -> List[OntologyNestedElementT]:
        """
        Returns all the child nodes of this ontology tree node with the matching title and matching type if specified.
        Title in ontologies do not need to be unique, however, we recommend unique titles when creating ontologies.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the item. Only nodes that match this type will be returned.
        """
        return _get_elements_by_title(title, self.children, type_=type_)

    def get_child_by_title(
        self,
        title: str,
        type_: Optional[Type[OntologyNestedElementT]] = None,
    ) -> OntologyNestedElementT:
        """
        Returns a child node of this ontology tree node with the matching title and matching type if specified. If more
        than one child in this Object have the same title, then an error will be thrown. If no item is found, an error
        will be thrown as well.

        Args:
            title: The exact title of the child node to search for in the ontology.
            type_: The expected type of the child node. Only a node that matches this type will be returned.
        """
        found_items = self.get_children_by_title(title, type_)
        _assert_singular_result_list(found_items, title, type_)
        return found_items[0]


@dataclass
class OntologyNestedElement(OntologyElement):
    uid: NestedID


def _assert_singular_result_list(
    found_items: Sequence[OntologyElement],
    title: str,
    type_: Any,
) -> None:
    if len(found_items) == 0:
        raise OntologyError(f"No item was found in the ontology with the given title `{title}` and type `{type_}`")
    elif len(found_items) > 1:
        raise OntologyError(
            f"More than one item was found in the ontology with the given title `{title}` and type `{type_}`. "
            f"Use the `get_children_by_title` or `get_child_by_hash` function instead. "
            f"The found items are `{found_items}`."
        )


def _get_element_by_hash(
    feature_node_hash: str, elements: Iterable[OntologyElement], type_: Optional[Type[OntologyNestedElementT]] = None
) -> Optional[OntologyNestedElementT]:
    for element in elements:
        if element.feature_node_hash == feature_node_hash:
            return checked_cast(element, type_)

        found_item = _get_element_by_hash(feature_node_hash, element.children, type_=type_)
        if found_item is not None:
            return found_item

    return None


def _get_elements_by_title(
    title: str, elements: Iterable[OntologyElement], type_: Optional[Type[OntologyNestedElementT]] = None
) -> List[OntologyNestedElementT]:
    res: List[OntologyNestedElementT] = []
    for element in elements:
        if element.title == title and does_type_match(element, type_):
            res.append(cast(OntologyNestedElementT, element))

        found_items = _get_elements_by_title(title, element.children, type_=type_)
        res.extend(found_items)

    return res
