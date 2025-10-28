from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, TypeVar, Any

from encord.constants.enums import SpaceType
from encord.objects.spaces.entity import ClassificationEntity, ObjectEntity
from encord.orm.label_space import LabelBlob, SpaceInfo

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance
    from encord.objects.ontology_labels_impl import LabelRowV2

SpaceT = TypeVar("SpaceT", bound="Space")


class Space(ABC):
    """Manages the objects on a space within LabelRowV2.

    Users should not instantiate this class directly, but must obtain these instances via LabelRow.list_spaces().
    """

    def __init__(self, space_id: str, title: str, space_type: SpaceType, parent: LabelRowV2):
        self.space_id = space_id
        self.title = title
        self.space_type = space_type
        self.parent = parent

    @abstractmethod
    def get_object_entities(
        self,
    ) -> list[ObjectEntity]:
        pass

    @abstractmethod
    def get_classification_entities(
        self,
    ) -> list[ClassificationEntity]:
        pass

    @abstractmethod
    def place_object_entity(self, entity: ObjectEntity, **kwargs: Any):
        """All implementations must accept 'data' as first param"""
        pass

    @abstractmethod
    def place_classification_entity(self, entity: ClassificationEntity, **kwargs: Any):
        """All implementations must accept 'data' as first param"""
        pass

    @abstractmethod
    def remove_object_entity(self, object_hash: str) -> Optional[ObjectEntity]:
        pass

    @abstractmethod
    def remove_classification_entity(self, classification_hash: str) -> Optional[ClassificationEntity]:
        pass

    @abstractmethod
    def _parse_space_dict(self, space_info: SpaceInfo, object_answers: dict, classification_answers: dict) -> None:
        pass

    @abstractmethod
    def _to_space_dict(self) -> SpaceInfo:
        pass

    @abstractmethod
    def _to_object_answers(self):
        pass

    @abstractmethod
    def _to_classification_answers(self):
        pass
