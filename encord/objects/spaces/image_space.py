from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Sequence, cast

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.coordinates import (
    GeometricCoordinates,
    add_coordinates_to_frame_object_dict,
    get_geometric_coordinates_from_frame_object_dict,
)
from encord.objects.label_utils import create_frame_classification_dict, create_frame_object_dict
from encord.objects.spaces.annotation.base_annotation import (
    AnnotationData,
    AnnotationMetadata,
)
from encord.objects.spaces.annotation.geometric_annotation import (
    GeometricAnnotationData,
    GeometricObjectAnnotation,
    SingleFrameClassificationAnnotation,
)
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.types import ChildInfo, ImageSpaceInfo, SpaceInfo
from encord.objects.spaces.video_space import FrameOverlapStrategy
from encord.objects.types import (
    AttributeDict,
    ClassificationAnswer,
    FrameClassification,
    FrameObject,
    LabelBlob,
    ObjectAnswer,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects import Classification, ClassificationInstance, ObjectInstance
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object


class ImageSpace(Space):
    """Image space implementation for single-frame image annotations."""

    def __init__(self, space_id: str, label_row: LabelRowV2, child_info: ChildInfo, width: int, height: int):
        super().__init__(space_id, label_row)
        self._objects_map: dict[str, ObjectInstance] = dict()
        self._classification_ontologies: set[str] = set()
        self._classifications_map: dict[str, ClassificationInstance] = dict()
        self._object_hash_to_annotation_data: dict[str, GeometricAnnotationData] = dict()
        self._classification_hash_to_annotation_data: dict[str, AnnotationData] = dict()

        self._layout_key = child_info["layout_key"]
        self._is_readonly = child_info["is_readonly"]
        self._file_name = child_info["file_name"]

        self._width = width
        self._height = height

    @property
    def layout_key(self) -> str:
        return self._layout_key

    @property
    def is_readonly(self) -> bool:
        return self._is_readonly

    def put_object_instance(
        self,
        object_instance: ObjectInstance,
        coordinates: GeometricCoordinates,
        *,
        on_overlap: FrameOverlapStrategy = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        self._method_not_supported_for_object_instance_with_frames(object_instance=object_instance)
        self._method_not_supported_for_object_instance_with_dynamic_attributes(object_instance=object_instance)

        already_exists = object_instance.object_hash in self._objects_map

        if already_exists and on_overlap == "error":
            raise LabelRowError(
                f"Annotation for object instance {object_instance.object_hash} already exists. Set 'on_overlap' to 'replace' to overwrite existing annotations."
            )

        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._add_to_space(self)

        frame_annotation_data = GeometricAnnotationData(
            annotation_metadata=AnnotationMetadata(),
            coordinates=coordinates,
        )

        frame_annotation_data.annotation_metadata.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

        self._object_hash_to_annotation_data[object_instance.object_hash] = frame_annotation_data

    def put_classification_instance(
        self,
        classification_instance: ClassificationInstance,
        *,
        on_overlap: FrameOverlapStrategy = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        self._method_not_supported_for_classification_instance_with_frames(
            classification_instance=classification_instance
        )

        is_classification_of_same_ontology_present = (
            classification_instance._ontology_classification.feature_node_hash in self._classification_ontologies
        )

        if is_classification_of_same_ontology_present:
            if on_overlap == "error":
                raise LabelRowError(
                    f"A classification instance for the classification with feature hash '{classification_instance._ontology_classification.feature_node_hash}' already exists. Set 'on_overlap' parameter to 'replace' to overwrite."
                )
            elif on_overlap == "replace":
                # Remove classification instances of that ontology item
                classification_hash_to_remove = None
                for existing_classification_instance in self._classifications_map.values():
                    if (
                        existing_classification_instance._ontology_classification.feature_node_hash
                        == classification_instance._ontology_classification.feature_node_hash
                    ):
                        classification_hash_to_remove = existing_classification_instance.classification_hash

                if classification_hash_to_remove is not None:
                    self._classifications_map.pop(classification_hash_to_remove)
                    self._classification_hash_to_annotation_data.pop(classification_hash_to_remove)

        self._classifications_map[classification_instance.classification_hash] = classification_instance
        self._classification_ontologies.add(classification_instance._ontology_classification.feature_node_hash)
        classification_instance._add_to_space(self)

        existing_frame_classification_annotation_data = self._classification_hash_to_annotation_data.get(
            classification_instance.classification_hash
        )

        if existing_frame_classification_annotation_data is None:
            existing_frame_classification_annotation_data = AnnotationData(
                annotation_metadata=AnnotationMetadata(),
            )

            self._classification_hash_to_annotation_data[classification_instance.classification_hash] = (
                existing_frame_classification_annotation_data
            )

        existing_frame_classification_annotation_data.annotation_metadata.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

    def get_object_instance_annotations(
        self, filter_object_instances: Optional[list[str]] = None
    ) -> Sequence[GeometricObjectAnnotation]:
        res: list[GeometricObjectAnnotation] = []

        for obj_hash, annotation in self._object_hash_to_annotation_data.items():
            if filter_object_instances is None or obj_hash in filter_object_instances:
                res.append(GeometricObjectAnnotation(space=self, object_instance=self._objects_map[obj_hash]))

        return res

    def get_classification_instance_annotations(
        self, filter_classification_instances: Optional[list[str]] = None
    ) -> list[SingleFrameClassificationAnnotation]:
        res: list[SingleFrameClassificationAnnotation] = []

        for classification_hash, annotation_data in dict(self._classification_hash_to_annotation_data.items()).items():
            if filter_classification_instances is None or classification_hash in filter_classification_instances:
                res.append(
                    SingleFrameClassificationAnnotation(
                        space=self,
                        classification_instance=self._classifications_map[classification_hash],
                    )
                )

        return res

    def get_object_instances(self) -> list[ObjectInstance]:
        return list(self._objects_map.values())

    def get_classification_instances(self) -> list[ClassificationInstance]:
        return list(self._classifications_map.values())

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        object_instance = self._objects_map.pop(object_hash, None)
        self._object_hash_to_annotation_data.pop(object_hash)

        if object_instance is not None:
            object_instance._remove_from_space(self.space_id)

        return object_instance

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        classification_instance = self._classifications_map.pop(classification_hash, None)

        if classification_instance is not None:
            classification_instance._remove_from_space(self.space_id)
            self._classification_hash_to_annotation_data.pop(classification_hash)
            self._classification_ontologies.remove(classification_instance._ontology_classification.feature_node_hash)

        return classification_instance

    """INTERNAL METHODS FOR DESERDE"""

    def _create_new_object_from_frame_object_dict(self, frame_object_label: FrameObject) -> ObjectInstance:
        from encord.objects.ontology_object import Object, ObjectInstance

        ontology = self._label_row._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)
        return ObjectInstance(ontology_object=label_class, object_hash=object_hash)

    def _create_new_classification_from_frame_label_dict(
        self, frame_classification_label: FrameClassification, classification_answers: dict
    ) -> Optional[ClassificationInstance]:
        from encord.objects import Classification, ClassificationInstance

        ontology = self._label_row._ontology.structure
        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Classification)

        # TODO: Probably can remove this check?
        if classification_answer := classification_answers.get(classification_hash):
            new_classification_instance = ClassificationInstance(
                ontology_classification=label_class, classification_hash=classification_hash
            )
            answers_dict = classification_answer["classifications"]
            self._label_row._add_static_answers_from_dict(new_classification_instance, answers_dict)

            return new_classification_instance

        return None

    def _to_encord_object(
        self,
        object_instance: ObjectInstance,
        frame_object_annotation_data: GeometricAnnotationData,
    ) -> FrameObject:
        from encord.objects.ontology_object import Object

        ontology_hash = object_instance._ontology_object.feature_node_hash
        ontology_object = self._label_row._ontology.structure.get_child_by_hash(ontology_hash, type_=Object)

        frame_object_dict = create_frame_object_dict(
            ontology_object=ontology_object,
            object_hash=object_instance.object_hash,
            object_instance_annotation=frame_object_annotation_data.annotation_metadata,
        )

        frame_object_dict = add_coordinates_to_frame_object_dict(
            coordinates=frame_object_annotation_data.coordinates,
            base_frame_object=frame_object_dict,
            width=self._width,
            height=self._height,
        )

        return frame_object_dict

    def _to_encord_classification(
        self,
        classification_instance: ClassificationInstance,
        frame_classification_annotation_data: AnnotationData,
    ) -> FrameClassification:
        from encord.objects import Classification
        from encord.objects.attributes import Attribute

        ontology_hash = classification_instance._ontology_classification.feature_node_hash
        ontology_classification = self._label_row._ontology.structure.get_child_by_hash(
            ontology_hash, type_=Classification
        )

        attribute_hash = classification_instance.ontology_item.attributes[0].feature_node_hash
        attribute = self._label_row._ontology.structure.get_child_by_hash(attribute_hash, type_=Attribute)

        frame_object_dict = create_frame_classification_dict(
            ontology_classification=ontology_classification,
            classification_instance_annotation=frame_classification_annotation_data.annotation_metadata,
            classification_hash=classification_instance.classification_hash,
            attribute=attribute,
        )

        return frame_object_dict

    def _build_frame_label_dict(self) -> LabelBlob:
        object_list = []
        classification_list = []

        for object_hash, frame_object_annotation_data in self._object_hash_to_annotation_data.items():
            space_object = self._objects_map[object_hash]
            object_list.append(
                self._to_encord_object(
                    object_instance=space_object, frame_object_annotation_data=frame_object_annotation_data
                )
            )

        for (
            classification_hash,
            frame_classification_annotation_data,
        ) in self._classification_hash_to_annotation_data.items():
            space_classification = self._classifications_map[classification_hash]
            classification_list.append(
                self._to_encord_classification(
                    classification_instance=space_classification,
                    frame_classification_annotation_data=frame_classification_annotation_data,
                )
            )

        return LabelBlob(
            objects=object_list,
            classifications=classification_list,
        )

    def _to_space_dict(self) -> ImageSpaceInfo:
        """Export image space to dictionary format."""
        label_hashes: list[str] = list(self._objects_map.keys())
        label_hashes.extend(list(self._classifications_map.keys()))
        frame_label = self._build_frame_label_dict()
        return ImageSpaceInfo(
            space_type=SpaceType.IMAGE,
            width=self._width,
            height=self._height,
            labels={
                "0": frame_label,
            },
            info={
                "is_readonly": self._is_readonly,
                "layout_key": self._layout_key,
                "file_name": self._file_name,
            },
        )

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, ObjectAnswer],
        classification_answers: dict[str, ClassificationAnswer],
    ) -> None:
        frame_label = space_info["labels"].get("0")
        if frame_label is not None:
            self._parse_frame_label_dict(frame_label=frame_label, classification_answers=classification_answers)

    def _parse_frame_label_dict(self, frame_label: LabelBlob, classification_answers: dict[str, ClassificationAnswer]):
        for frame_object_label in frame_label["objects"]:
            object_hash = frame_object_label["objectHash"]
            object_instance = None

            for space in self._label_row._space_map.values():
                object_instance = space._objects_map.get(object_hash)
                if object_instance is not None:
                    break

            if object_instance is None:
                object_instance = self._create_new_object_from_frame_object_dict(frame_object_label=frame_object_label)

            coordinates: GeometricCoordinates = get_geometric_coordinates_from_frame_object_dict(frame_object_label)

            object_frame_instance_info = AnnotationMetadata.from_dict(frame_object_label)
            self.put_object_instance(
                object_instance=object_instance,
                coordinates=coordinates,
                created_at=object_frame_instance_info.created_at,
                created_by=object_frame_instance_info.created_by,
                last_edited_at=object_frame_instance_info.last_edited_at,
                last_edited_by=object_frame_instance_info.last_edited_by,
                manual_annotation=object_frame_instance_info.manual_annotation,
                confidence=object_frame_instance_info.confidence,
            )

        # Process classifications
        for classification in frame_label["classifications"]:
            classification_hash = classification["classificationHash"]
            entity = self._label_row._space_classifications_map.get(classification_hash)

            if entity is None:
                entity = self._create_new_classification_from_frame_label_dict(
                    frame_classification_label=classification, classification_answers=classification_answers
                )

            if entity is None:
                continue

            classification_frame_instance_info = AnnotationMetadata.from_dict(classification)
            self.put_classification_instance(
                entity,
                created_at=classification_frame_instance_info.created_at,
                created_by=classification_frame_instance_info.created_by,
                last_edited_at=classification_frame_instance_info.last_edited_at,
                last_edited_by=classification_frame_instance_info.last_edited_by,
                manual_annotation=classification_frame_instance_info.manual_annotation,
                confidence=classification_frame_instance_info.confidence,
            )

    def _to_object_answers(self) -> dict[str, ObjectAnswer]:
        ret: dict[str, ObjectAnswer] = {}
        for object_instance in self.get_object_instances():
            all_static_answers = self._label_row._get_all_static_answers(object_instance)
            object_index_element: ObjectAnswer = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": object_instance.object_hash,
            }
            ret[object_instance.object_hash] = object_index_element

        return ret

    def _to_classification_answers(self) -> dict[str, ClassificationAnswer]:
        ret: dict[str, ClassificationAnswer] = {}
        for classification in self.get_classification_instances():
            all_static_answers = classification.get_all_static_answers()
            classifications: list[AttributeDict] = [
                cast(AttributeDict, answer.to_encord_dict()) for answer in all_static_answers if answer.is_answered()
            ]
            classification_index_element: ClassificationAnswer = {
                "classifications": classifications,
                "classificationHash": classification.classification_hash,
                "featureHash": classification.feature_hash,
            }

            ret[classification.classification_hash] = classification_index_element

        return ret
