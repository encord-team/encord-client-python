from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Dict,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.spaces.annotation.base_annotation import ClassificationAnnotation, ObjectAnnotation
from encord.objects.spaces.types import SpaceInfo
from encord.objects.types import ClassificationAnswer, ObjectAnswerForGeometric, ObjectAnswerForNonGeometric

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance
    from encord.objects.ontology_labels_impl import LabelRowV2

SpaceT = TypeVar("SpaceT", bound="Space")


class Space(ABC):
    """
    Manages the objects on a space within LabelRowV2.
    Users should not instantiate this class directly, but must obtain these instances via LabelRow.list_spaces().
    """

    space_id: str
    _label_row: LabelRowV2
    _objects_map: dict[str, ObjectInstance]
    _classifications_map: dict[str, ClassificationInstance]

    def __init__(self, space_id: str, label_row: LabelRowV2):
        self.space_id = space_id
        self._label_row = label_row
        self._objects_map: dict[str, ObjectInstance] = dict()
        self._classifications_map: dict[str, ClassificationInstance] = dict()

    @abstractmethod
    def get_object_instances(
        self,
    ) -> list[ObjectInstance]:
        pass

    @abstractmethod
    def get_classification_instances(
        self,
    ) -> list[ClassificationInstance]:
        pass

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        pass

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        pass

    @abstractmethod
    def get_object_instance_annotations(
        self, filter_object_instances: Optional[list[str]] = None
    ) -> Sequence[ObjectAnnotation]:
        pass

    @abstractmethod
    def get_classification_instance_annotations(
        self, filter_classification_instances: Optional[list[str]] = None
    ) -> Sequence[ClassificationAnnotation]:
        pass

    @abstractmethod
    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, Union[ObjectAnswerForGeometric, ObjectAnswerForNonGeometric]],
        classification_answers: dict[str, ClassificationAnswer],
    ) -> None:
        pass

    @abstractmethod
    def _to_space_dict(self) -> SpaceInfo:
        pass

    @abstractmethod
    def _to_object_answers(
        self, existing_object_answers: Dict[str, Union[ObjectAnswerForGeometric, ObjectAnswerForNonGeometric]]
    ) -> Dict[str, Union[ObjectAnswerForGeometric, ObjectAnswerForNonGeometric]]:
        pass

    @abstractmethod
    def _to_classification_answers(
        self, existing_classification_answers: Dict[str, ClassificationAnswer]
    ) -> Dict[str, ClassificationAnswer]:
        pass

    @staticmethod
    def _method_not_supported_for_object_instance_with_frames(object_instance: ObjectInstance):
        if len(object_instance._frames_to_instance_data) > 0:
            raise LabelRowError(
                "Object instance contains frames data. "
                "Ensure ObjectInstance.set_for_frames was not used before calling this method. "
            )

    @staticmethod
    def _method_not_supported_for_object_instance_with_dynamic_attributes(object_instance: ObjectInstance):
        if len(object_instance._get_all_dynamic_answers()) > 0:
            raise LabelRowError(
                "Object instance contains dynamic attributes. "
                "Please ensure no dynamic attributes were set on this ObjectInstance. "
            )

    @staticmethod
    def _method_not_supported_for_classification_instance_with_frames(classification_instance: ClassificationInstance):
        if len(classification_instance._frames_to_data) > 0:
            raise LabelRowError(
                "Classification instance contains frames data. "
                "Ensure ClassificationInstance.set_for_frames was not used before calling this method. "
            )
