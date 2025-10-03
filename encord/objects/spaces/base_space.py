from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, TypeVar

from encord.constants.enums import SpaceType
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
    def get_object_instances(
        self,
    ) -> list[ObjectInstance]:
        pass

    @abstractmethod
    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        pass

    @abstractmethod
    def move_object_instance_from_space(self, object_to_move: ObjectInstance) -> Optional[ObjectInstance]:
        pass

    @abstractmethod
    def get_classification_instances(
        self,
    ) -> list[ClassificationInstance]:
        pass

    @abstractmethod
    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        pass

    @abstractmethod
    def move_classification_instance_from_space(
        self, classification_to_move: ClassificationInstance
    ) -> Optional[ClassificationInstance]:
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

    @abstractmethod
    def _on_set_for_frames(self, frame: int, object_hash: str):
        """
            Users can still call object_instance.set_for_frames or classification_instance.set_for_frames.
            This will be the callback which is called when that happens.
        """
        pass
