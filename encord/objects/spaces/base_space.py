from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, TypeVar

from encord.constants.enums import SpaceType
from encord.objects.coordinates import Coordinates
from encord.objects.spaces.space_entity import ObjectInstance, SpaceClassification
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
        self._objects_map: dict[str, ObjectInstance] = dict()

    @abstractmethod
    def get_objects(
        self,
    ) -> list[ObjectInstance]:
        pass

    @abstractmethod
    def get_classifications(
        self,
    ) -> list[SpaceClassification]:
        pass

    @abstractmethod
    def place_object(self, object: ObjectInstance, coordinates: Coordinates, **kwargs: Any):
        pass

    @abstractmethod
    def place_classification(self, classification: SpaceClassification, **kwargs: Any):
        pass

    @abstractmethod
    def remove_space_object(self, object_hash: str) -> Optional[ObjectInstance]:
        pass

    @abstractmethod
    def remove_space_classification(self, classification_hash: str) -> Optional[SpaceClassification]:
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
