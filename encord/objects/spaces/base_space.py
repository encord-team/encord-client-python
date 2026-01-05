from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Dict,
    Generic,
    Iterator,
    Literal,
    Optional,
    TypeVar,
    Union,
)

from pytest import Class

from encord.exceptions import LabelRowError
from encord.objects.spaces.annotation.base_annotation import (
    _AnnotationData,
    _AnnotationMetadata,
    _ClassificationAnnotation,
    _ObjectAnnotation,
)
from encord.objects.spaces.annotation.global_annotation import GlobalClassificationAnnotation
from encord.objects.spaces.types import SpaceInfo
from encord.objects.types import (
    ClassificationAnswer,
    ObjectAnswer,
    ObjectAnswerForGeometric,
    ObjectAnswerForNonGeometric,
)

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance
    from encord.objects.ontology_labels_impl import LabelRowV2

SpaceT = TypeVar("SpaceT", bound="Space")

# Type variables for generic annotation types
ObjectAnnotationT = TypeVar("ObjectAnnotationT", bound="_ObjectAnnotation")
ClassificationAnnotationT = TypeVar("ClassificationAnnotationT", bound="_ClassificationAnnotation")
ClassificationOverlapStrategyT = TypeVar("ClassificationOverlapStrategyT", bound="str")

GlobalClassificationOverlapStrategy = Union[Literal["error"], Literal["replace"]]


class Space(ABC, Generic[ObjectAnnotationT, ClassificationAnnotationT, ClassificationOverlapStrategyT]):
    """
    Manages the objects on a space within LabelRowV2.
    Users should not instantiate this class directly, but must obtain these instances via LabelRow.list_spaces().
    """

    space_id: str
    _label_row: LabelRowV2
    _objects_map: dict[str, ObjectInstance]
    _classifications_map: dict[str, ClassificationInstance]
    _global_classification_hash_to_annotation_data: dict[str, _AnnotationData]

    # Used to keep track of global classifications that already exist.
    _global_classification_ontology_feature_hashes: set[str]

    def __init__(self, space_id: str, label_row: LabelRowV2):
        self.space_id = space_id
        self._label_row = label_row
        self._objects_map: dict[str, ObjectInstance] = dict()
        self._classifications_map: dict[str, ClassificationInstance] = dict()
        self._global_classification_hash_to_annotation_data = {}
        self._global_classification_ontology_feature_hashes = set()

    def get_object_instances(self) -> list[ObjectInstance]:
        """Get all object instances in the space.

        Returns:
            list[ObjectInstance]: List of all object instances present in the space.
        """
        self._label_row._check_labelling_is_initalised()
        return list(self._objects_map.values())

    def get_classification_instances(self) -> list[ClassificationInstance]:
        """Get all classification instances in the space.

        Returns:
            list[ClassificationInstance]: List of all classification instances present in the space.
        """
        self._label_row._check_labelling_is_initalised()
        return list(self._classifications_map.values())

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        pass

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        pass

    def get_object_instance_annotations(
        self, filter_object_instances: Optional[list[str]] = None
    ) -> Iterator[ObjectAnnotationT]:
        """Get all object instance annotations in the space.

        Args:
            filter_object_instances: Optional list of object hashes to filter by.
                If provided, only annotations for these objects will be returned.

        Returns:
            Iterator[ObjectAnnotationT]: Iterator over all object annotations in the space.
                The concrete type depends on the Space subclass.
                Annotations are created lazily as the iterator is consumed.
        """
        self._label_row._check_labelling_is_initalised()
        filter_set = set(filter_object_instances) if filter_object_instances is not None else None

        return (
            self._create_object_annotation(obj_hash)
            for obj_hash in self._objects_map
            if filter_set is None or obj_hash in filter_set
        )

    def get_classification_instance_annotations(
        self, filter_classification_instances: Optional[list[str]] = None
    ) -> Iterator[Union[ClassificationAnnotationT, GlobalClassificationAnnotation]]:
        """Get all classification instance annotations in the space.

        Args:
            filter_classification_instances: Optional list of classification hashes to filter by.
                If provided, only annotations for these classifications will be returned.

        Returns:
            Iterator[ClassificationAnnotationT]: Iterator over all classification annotations in the space.
                The concrete type depends on the Space subclass.
                Annotations are created lazily as the iterator is consumed.
        """
        self._label_row._check_labelling_is_initalised()
        filter_set = set(filter_classification_instances) if filter_classification_instances is not None else None

        non_global_annotations = (
            self._create_classification_annotation(classification_hash)
            for classification_hash in self._classifications_map
            if filter_set is None or classification_hash in filter_set
        )

        global_annotations = (
            GlobalClassificationAnnotation(
                space=self,
                classification_instance=self._classifications_map[classification_hash],
            )
            for classification_hash in self._global_classification_hash_to_annotation_data
            if filter_set is None or classification_hash in filter_set
        )

        return chain(non_global_annotations, global_annotations)

    def _put_global_classification_instance(
        self,
        classification_instance: ClassificationInstance,
        *,
        on_overlap: Optional[GlobalClassificationOverlapStrategy],
        created_at: Optional[datetime],
        created_by: Optional[str],
        last_edited_at: Optional[datetime],
        last_edited_by: Optional[str],
        confidence: Optional[float],
        manual_annotation: Optional[bool],
    ) -> None:
        is_present = classification_instance.feature_hash in self._global_classification_ontology_feature_hashes

        if is_present:
            if on_overlap == "error":
                raise LabelRowError(
                    f"The classification '{classification_instance.classification_hash}' already exists globally."
                    f"Set 'on_overlap' parameter to 'replace' to overwrite."
                )
            elif on_overlap == "replace":
                # If overwriting, remove conflicting classification entries from other classification instances
                self._remove_global_classification_instance(classification=classification_instance)

        self._classifications_map[classification_instance.classification_hash] = classification_instance
        new_classification_annotation_data = _AnnotationData(
            annotation_metadata=_AnnotationMetadata(),
        )
        new_classification_annotation_data.annotation_metadata.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

        self._global_classification_hash_to_annotation_data[classification_instance.classification_hash] = (
            new_classification_annotation_data
        )

    def _remove_global_classification_instance(
        self,
        classification: ClassificationInstance,
    ) -> ClassificationInstance:
        classification._remove_from_space(self.space_id)
        self._global_classification_ontology_feature_hashes.remove(classification.feature_hash)
        self._global_classification_hash_to_annotation_data.pop(classification.classification_hash)
        self._classifications_map.pop(classification.classification_hash)

        return classification

    @abstractmethod
    def put_classification_instance(
        self,
        classification_instance: ClassificationInstance,
        *,
        on_overlap: Optional[ClassificationOverlapStrategyT] = None,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        pass

    @abstractmethod
    def _create_object_annotation(self, obj_hash: str) -> ObjectAnnotationT:
        """Factory method to create the appropriate object annotation type for this space.

        Args:
            obj_hash: The hash of the object instance.

        Returns:
            ObjectAnnotationT: The concrete annotation type for this space.
        """
        pass

    @abstractmethod
    def _create_classification_annotation(self, classification_hash: str) -> ClassificationAnnotationT:
        """Factory method to create the appropriate classification annotation type for this space.

        Args:
            classification_hash: The hash of the classification instance.

        Returns:
            ClassificationAnnotationT: The concrete annotation type for this space.
        """
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
    def _to_object_answers(self, existing_object_answers: Dict[str, ObjectAnswer]) -> Dict[str, ObjectAnswer]:
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
