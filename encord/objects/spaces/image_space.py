from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional, Sequence, cast

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.coordinates import (
    GeometricCoordinates,
    add_coordinates_to_frame_object_dict,
    get_geometric_coordinates_from_frame_object_dict,
)
from encord.objects.label_utils import create_frame_classification_dict, create_frame_object_dict
from encord.objects.spaces.annotation.base_annotation import (
    _AnnotationData,
    _AnnotationMetadata,
)
from encord.objects.spaces.annotation.geometric_annotation import (
    _GeometricAnnotationData,
    _GeometricObjectAnnotation,
)
from encord.objects.spaces.annotation.global_annotation import _GlobalClassificationAnnotation
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.multiframe_space.multiframe_space import FrameOverlapStrategy
from encord.objects.spaces.types import ImageSpaceInfo, SpaceInfo
from encord.objects.types import (
    AttributeDict,
    ClassificationAnswer,
    FrameClassification,
    FrameObject,
    LabelBlob,
    ObjectAnswer,
    ObjectAnswerForGeometric,
    _is_global_classification_on_space,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance
    from encord.objects.ontology_labels_impl import LabelRowV2


class ImageSpace(Space[_GeometricObjectAnnotation, _GlobalClassificationAnnotation, FrameOverlapStrategy]):
    """Image space implementation for single-frame image annotations."""

    def __init__(self, space_id: str, label_row: LabelRowV2, space_info: SpaceInfo, width: int, height: int):
        super().__init__(space_id, label_row, space_info)
        self._object_hash_to_annotation_data: dict[str, _GeometricAnnotationData] = dict()

        self._width = width
        self._height = height

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
        """Add an object instance to the image space.

        Args:
            object_instance: The object instance to add to the image space.
            coordinates: Geometric coordinates for the object (e.g., bounding box, polygon, polyline).
            on_overlap: Strategy for handling existing annotations.
                - "error" (default): Raises an error if annotation already exists.
                - "replace": Overwrites existing annotations.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If annotation already exists when on_overlap="error".
        """
        self._label_row._check_labelling_is_initalised()
        self._method_not_supported_for_object_instance_with_frames(object_instance=object_instance)
        self._method_not_supported_for_object_instance_with_dynamic_attributes(object_instance=object_instance)

        already_exists = object_instance.object_hash in self._objects_map

        if already_exists and on_overlap == "error":
            raise LabelRowError(
                f"Annotation for object instance {object_instance.object_hash} already exists. Set 'on_overlap' to 'replace' to overwrite existing annotations."
            )

        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._add_to_space(self)

        frame_annotation_data = _GeometricAnnotationData(
            annotation_metadata=_AnnotationMetadata(),
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
        on_overlap: Optional[FrameOverlapStrategy] = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Add a classification instance to the image space.

        Args:
            classification_instance: The classification instance to add to the image space.
            on_overlap: Strategy for handling existing classifications.
                - "error" (default): Raises an error if classification of the same ontology item already exists.
                - "replace": Overwrites existing classifications.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If classification already exists when on_overlap="error".
        """
        self._label_row._check_labelling_is_initalised()
        self._method_not_supported_for_classification_instance_with_frames(
            classification_instance=classification_instance
        )

        self._put_global_classification_instance(
            classification_instance=classification_instance,
            on_overlap=on_overlap,
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

    def _create_object_annotation(self, obj_hash: str) -> _GeometricObjectAnnotation:
        return _GeometricObjectAnnotation(space=self, object_instance=self._objects_map[obj_hash])

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        """Remove an object instance from the image space.

        This removes the object and all associated data from the image space.

        Args:
            object_hash: The hash identifier of the object instance to remove.

        Returns:
            Optional[ObjectInstance]: The removed object instance, or None if the object wasn't found.
        """
        self._label_row._check_labelling_is_initalised()
        object_instance = self._objects_map.pop(object_hash, None)
        self._object_hash_to_annotation_data.pop(object_hash)

        if object_instance is not None:
            object_instance._remove_from_space(self.space_id)

        return object_instance

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        """Remove a classification instance from the image space.

        This removes the classification and all associated data from the image space.

        Args:
            classification_hash: The hash identifier of the classification instance to remove.

        Returns:
            Optional[ClassificationInstance]: The removed classification instance, or None if the classification wasn't found.
        """
        self._label_row._check_labelling_is_initalised()
        classification_instance = self._classifications_map[classification_hash]
        return self._remove_global_classification_instance(classification=classification_instance)

    """INTERNAL METHODS FOR DESERDE"""

    def _create_new_object_from_frame_object_dict(self, frame_object_label: FrameObject) -> ObjectInstance:
        from encord.objects.ontology_object import Object, ObjectInstance

        ontology = self._label_row._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)
        return ObjectInstance(ontology_object=label_class, object_hash=object_hash)

    def _create_new_classification_from_frame_label_dict(
        self, frame_classification_label: FrameClassification, classification_answers: Dict[str, ClassificationAnswer]
    ) -> Optional[ClassificationInstance]:
        from encord.objects import Classification, ClassificationInstance

        ontology = self._label_row._ontology.structure
        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Classification)

        classification_answer = classification_answers.get(classification_hash)
        if classification_answer is None:
            raise LabelRowError("Classification exists in frame labels, but not in classification answers.")

        new_classification_instance = ClassificationInstance(
            ontology_classification=label_class, classification_hash=classification_hash
        )
        answers_dict = classification_answer["classifications"]
        self._label_row._add_static_answers_from_dict(new_classification_instance, answers_dict)

        return new_classification_instance

    def _to_encord_object(
        self,
        object_instance: ObjectInstance,
        frame_object_annotation_data: _GeometricAnnotationData,
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
        frame_classification_annotation_data: _AnnotationData,
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
        ) in self._global_classification_hash_to_annotation_data.items():
            space_classification = self._classifications_map[classification_hash]
            if space_classification.is_global():
                continue

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
        )

    def _parse_space_dict(
        self,
        space_info: SpaceInfo,
        object_answers: dict[str, ObjectAnswerForGeometric],
        classification_answers: dict[str, ClassificationAnswer],
    ) -> None:
        space_labels = cast(Dict[str, LabelBlob], space_info.get("labels"))
        frame_label = space_labels.get("0")
        if frame_label is not None:
            self._parse_frame_label_dict(frame_label=frame_label, classification_answers=classification_answers)

        for answer in object_answers.values():
            object_hash = answer["objectHash"]
            if object_instance := self._objects_map.get(object_hash):
                answer_list = answer["classifications"]
                object_instance.set_answer_from_list(answer_list)

        for classification_answer in classification_answers.values():
            spaces = classification_answer.get("spaces", {})
            space_range = spaces.get(self.space_id, None)
            if space_range is not None and _is_global_classification_on_space(space_range=space_range):
                classification_instance = self._label_row._create_new_classification_instance_from_answer(
                    classification_answer
                )

                if classification_instance is None:
                    continue

                annotation_metadata = _AnnotationMetadata.from_dict(classification_answer)
                self._put_global_classification_instance(
                    classification_instance=classification_instance,
                    on_overlap="replace",
                    created_at=annotation_metadata.created_at,
                    created_by=annotation_metadata.created_by,
                    last_edited_at=annotation_metadata.last_edited_at,
                    last_edited_by=annotation_metadata.last_edited_by,
                    confidence=annotation_metadata.confidence,
                    manual_annotation=annotation_metadata.manual_annotation,
                )

    def _parse_frame_label_dict(self, frame_label: LabelBlob, classification_answers: dict[str, ClassificationAnswer]):
        for frame_object_label in frame_label["objects"]:
            object_hash = frame_object_label["objectHash"]
            object_instance = None

            # TODO: Think about how to make this more efficient
            for space in self._label_row._space_map.values():
                object_instance = space._objects_map.get(object_hash)
                if object_instance is not None:
                    break

            if object_instance is None:
                object_instance = self._create_new_object_from_frame_object_dict(frame_object_label=frame_object_label)

            coordinates: GeometricCoordinates = get_geometric_coordinates_from_frame_object_dict(frame_object_label)

            object_frame_instance_info = _AnnotationMetadata.from_dict(frame_object_label)
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

            classification_frame_instance_info = _AnnotationMetadata.from_dict(classification)
            self.put_classification_instance(
                entity,
                created_at=classification_frame_instance_info.created_at,
                created_by=classification_frame_instance_info.created_by,
                last_edited_at=classification_frame_instance_info.last_edited_at,
                last_edited_by=classification_frame_instance_info.last_edited_by,
                manual_annotation=classification_frame_instance_info.manual_annotation,
                confidence=classification_frame_instance_info.confidence,
            )

    def _to_object_answers(self, existing_object_answers: Dict[str, ObjectAnswer]) -> Dict[str, ObjectAnswer]:
        ret: dict[str, ObjectAnswerForGeometric] = {}
        for object_instance in self.get_object_instances():
            all_static_answers = self._label_row._get_all_static_answers(object_instance)
            object_index_element: ObjectAnswerForGeometric = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": object_instance.object_hash,
            }
            ret[object_instance.object_hash] = object_index_element

        return cast(Dict[str, ObjectAnswer], ret)

    def _to_classification_answers(
        self, existing_classification_answers: Dict[str, ClassificationAnswer]
    ) -> Dict[str, ClassificationAnswer]:
        ret: dict[str, ClassificationAnswer] = {}
        for classification in self.get_classification_instances():
            all_static_answers = classification.get_all_static_answers()
            classifications: list[AttributeDict] = [
                cast(AttributeDict, answer.to_encord_dict()) for answer in all_static_answers if answer.is_answered()
            ]

            if classification.is_global():
                ret[classification.classification_hash] = self._to_global_classification_answer(
                    classification_instance=classification,
                    classifications=classifications,
                    space_range={"range": [], "type": "frame"},
                )
            else:
                classification_index_element: ClassificationAnswer = {
                    "classifications": classifications,
                    "classificationHash": classification.classification_hash,
                    "featureHash": classification.feature_hash,
                    "spaces": {
                        self.space_id: {
                            "range": [[0, 0]],  # For images, there is only one frame
                            "type": "frame",
                        }
                    },
                }

                ret[classification.classification_hash] = classification_index_element

        return ret
