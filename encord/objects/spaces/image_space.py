from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from typing_extensions import Unpack

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects import Classification, ClassificationInstance
from encord.objects.coordinates import (
    TwoDimensionalCoordinates,
    add_coordinates_to_frame_object_dict,
)
from encord.objects.frames import Frames
from encord.objects.label_utils import create_frame_object_dict
from encord.objects.ontology_object_instance import (
    AddObjectInstanceParams,
)
from encord.objects.spaces.annotation.base_annotation import Annotation, AnnotationData, AnnotationInfo
from encord.objects.spaces.annotation.video_annotation import (
    FrameAnnotation,
    TwoDimensionalAnnotation,
    TwoDimensionalAnnotationData,
    TwoDimensionalFrameAnnotation,
)
from encord.objects.spaces.annotation_instance.base_instance import BaseObjectInstance
from encord.objects.spaces.annotation_instance.image_instance import ImageClassificationInstance, ImageObjectInstance
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.entity import ClassificationEntity, ObjectEntity
from encord.objects.spaces.types import FrameClassificationIndex, FrameObjectIndex
from encord.orm.label_space import ImageSpaceInfo, LabelBlob, SpaceInfo

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object


class ImageSpace(Space):
    """Image space implementation for single-frame image annotations."""

    def __init__(self, space_id: str, title: str, parent: LabelRowV2, width: int, height: int):
        super().__init__(space_id, title, SpaceType.IMAGE, parent)
        self._objects_map: dict[str, ImageObjectInstance] = dict()
        self._classifications_map: dict[str, ImageClassificationInstance] = dict()
        self._object_entities_map: dict[str, ObjectEntity] = dict()
        self._classification_entities_map: dict[str, ClassificationEntity] = dict()
        self._object_entity_hash_to_annotation_data: dict[str, TwoDimensionalAnnotationData] = dict()
        self._classification_entity_hash_to_annotation_data: dict[str, AnnotationData] = dict()

        self._width = width
        self._height = height

    def place_object_entity(
        self,
        entity: ObjectEntity,
        coordinates: TwoDimensionalCoordinates,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        self._object_entities_map[entity.object_hash] = entity
        entity._space_ids.add(self.space_id)

        # TODO: Check overwrites


        existing_frame_annotation_data = self._object_entity_hash_to_annotation_data.get(
           entity.object_hash
        )
        if existing_frame_annotation_data is None:
            existing_frame_annotation_data = TwoDimensionalAnnotationData(
                object_frame_instance_info=AnnotationInfo(),
                coordinates=coordinates,
            )

            self._object_entity_hash_to_annotation_data[entity.object_hash] = existing_frame_annotation_data


            existing_frame_annotation_data.object_frame_instance_info.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                reviews=reviews,
                is_deleted=is_deleted,
            )

    def place_classification_entity(
        self,
        entity: ClassificationEntity,
        *,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,
    ) -> None:
        self._classification_entities_map[entity.classification_hash] = entity
        entity._space_ids.add(self.space_id)

        # TODO: Check overwrites

        existing_frame_classification_annotation_data = self._classification_entity_hash_to_annotation_data.get(entity.classification_hash)
        if existing_frame_classification_annotation_data is None:
            existing_frame_classification_annotation_data = AnnotationData(
                object_frame_instance_info=AnnotationInfo(),
            )

            self._classification_entity_hash_to_annotation_data[entity.classification_hash] = existing_frame_classification_annotation_data

        existing_frame_classification_annotation_data.object_frame_instance_info.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            reviews=reviews,
        )

    def get_object_annotations(self) -> list[TwoDimensionalAnnotation]:
        res: list[TwoDimensionalAnnotation] = []

        for obj_hash, annotation in self._object_entity_hash_to_annotation_data.items():
            res.append(
                TwoDimensionalAnnotation(space=self, entity=self._object_entities_map[obj_hash])
            )

        return res

    def get_classification_annotations(self) -> list[Annotation]:
        res: list[Annotation] = []

        for frame, classification in dict(
            sorted(self._frames_to_classification_hash_to_annotation_data.items())
        ).items():
            for classification_hash, annotation in classification.items():
                res.append(
                    Annotation(
                        space=self, entity=self._classification_entities_map[classification_hash]
                    )
                )

        return res

    def get_object_entities(self) -> list[ObjectEntity]:
        return list(self._object_entities_map.values())

    def get_classification_entities(self) -> list[ClassificationEntity]:
        return list(self._classification_entities_map.values())

    def remove_object_entity(self, object_hash: str) -> Optional[ObjectEntity]:
        obj_entity = self._object_entities_map.pop(object_hash, None)
        for frame, obj in self._frames_to_entity_hash_to_annotation_data.items():
            if object_hash in obj:
                obj.pop(object_hash)

        return obj_entity

    def remove_classification_entity(self, classification_hash: str) -> Optional[ClassificationEntity]:
        classification_entity = self._classification_entities_map.pop(classification_hash, None)
        for frame, classification in self._frames_to_classification_hash_to_annotation_data.items():
            if classification_hash in classification:
                classification.pop(classification_hash)

        return classification_entity

    def _create_new_object_instance_from_frame_label_dict(self, frame_object_label: dict):
        from encord.objects.ontology_object import Object

        ontology = self.parent._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)

        object_instance = ImageObjectInstance(label_class, object_hash=object_hash, space=self)

        coordinates = self.parent._get_coordinates(frame_object_label)
        object_frame_instance_info = BaseObjectInstance.AnnotationInfo.from_dict(frame_object_label)
        object_instance.add_annotation(
            coordinates=coordinates,
            created_at=object_frame_instance_info.created_at,
            created_by=object_frame_instance_info.created_by,
            last_edited_at=object_frame_instance_info.last_edited_at,
            last_edited_by=object_frame_instance_info.last_edited_by,
            confidence=object_frame_instance_info.confidence,
            manual_annotation=object_frame_instance_info.manual_annotation,
            reviews=object_frame_instance_info.reviews,
            is_deleted=object_frame_instance_info.is_deleted,
        )
        return object_instance

    def _create_new_classification_instance_from_frame_label_dict(
        self, frame_classification_label: dict, classification_answers: dict
    ):
        from encord.objects.classification import Classification

        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]

        label_class = self.parent._ontology.structure.get_child_by_hash(feature_hash, type_=Classification)
        classification_instance = ImageClassificationInstance(
            label_class, classification_hash=classification_hash, space=self
        )

        frame_view = ClassificationInstance.FrameData.from_dict(frame_classification_label)
        classification_instance.set_annotation(
            created_at=frame_view.created_at,
            created_by=frame_view.created_by,
            confidence=frame_view.confidence,
            manual_annotation=frame_view.manual_annotation,
            last_edited_at=frame_view.last_edited_at,
            last_edited_by=frame_view.last_edited_by,
            reviews=frame_view.reviews,
        )

        # For some older label rows we might have a classification entry, but without an assigned answer.
        # These cases are equivalent to not having classifications at all, so just ignoring them
        if classification_answer := classification_answers.get(classification_hash):
            answers_dict = classification_answer["classifications"]
            self.parent._add_static_answers_from_dict(classification_instance, answers_dict)
            return classification_instance

        return None

    def _add_object_instance(self, object_instance: ImageObjectInstance) -> None:
        """Add an object instance to this space and track it across its frames."""
        self._objects_map[object_instance.object_hash] = object_instance

    def _add_classification_instance(self, classification_instance: ImageClassificationInstance) -> None:
        """Add a classification instance to this space and track it across its frames."""
        self._classifications_map[classification_instance.classification_hash] = classification_instance

    """INTERNAL METHODS FOR DESERDE"""

    def _to_encord_object(
        self,
        object_: ImageObjectInstance,
    ) -> Dict[str, Any]:
        from encord.objects.ontology_object import Object

        object_instance_annotation = object_.get_annotation()

        coordinates = object_instance_annotation.coordinates
        ontology_hash = object_.ontology_item.feature_node_hash
        ontology_object = self.parent._ontology.structure.get_child_by_hash(ontology_hash, type_=Object)

        frame_object_dict = create_frame_object_dict(
            ontology_object=ontology_object,
            object_instance=object_,
            object_instance_annotation=object_instance_annotation,
        )

        add_coordinates_to_frame_object_dict(
            coordinates=coordinates, frame_object_dict=frame_object_dict, width=self._width, height=self._height
        )

        return frame_object_dict

    def _build_frame_label_dict(self, label_hashes: set[str]) -> LabelBlob:
        object_list = []
        classification_list = []

        for label_hash in label_hashes:
            frame_object_instance = self._objects_map.get(label_hash)
            frame_classification_instance = self._classifications_map.get(label_hash)

            if frame_object_instance is None and frame_classification_instance is None:
                continue
            elif frame_object_instance is not None:
                object_list.append(self._to_encord_object(frame_object_instance))
            else:
                classification_list.append(
                    self.parent._to_encord_classification(frame_classification_instance, frame=0)
                )

        return LabelBlob(
            objects=object_list,
            classifications=classification_list,
        )

    def _to_space_dict(self) -> ImageSpaceInfo:
        """Export image space to dictionary format."""
        label_hashes: list[str] = list(self._objects_map.keys())
        label_hashes.extend(list(self._classifications_map.keys()))
        frame_label = self._build_frame_label_dict(label_hashes=set(label_hashes))
        return ImageSpaceInfo(
            space_type=self.space_type,
            width=self._width,
            height=self._height,
            labels={
                "0": frame_label,
            },
        )

    def _parse_space_dict(self, space_info: SpaceInfo, object_answers: dict, classification_answers: dict) -> None:
        frame_label = space_info["labels"].get("0")
        if frame_label is not None:
            self._parse_frame_label_dict(frame_label=frame_label, classification_answers=classification_answers)

    def _parse_frame_label_dict(self, frame_label: dict, classification_answers: dict):
        for obj in frame_label["objects"]:
            object_hash = obj["objectHash"]
            if object_hash not in self._objects_map:
                new_object_instance = self._create_new_object_instance_from_frame_label_dict(obj)
                self._add_object_instance(new_object_instance)
            else:
                raise LabelRowError("Duplicate object hash in frame label.")

        # Process classifications
        for classification in frame_label["classifications"]:
            classification_hash = classification["classificationHash"]
            if classification_hash not in self._classifications_map:
                new_classification_instance = self._create_new_classification_instance_from_frame_label_dict(
                    classification, classification_answers
                )
                self._add_classification_instance(new_classification_instance)
            else:
                classification_instance = self._classifications_map[classification_hash]
                classification_frame_instance_info = ClassificationInstance.FrameData.from_dict(classification)

                classification_instance.set_annotation(
                    created_at=classification_frame_instance_info.created_at,
                    created_by=classification_frame_instance_info.created_by,
                    last_edited_at=classification_frame_instance_info.last_edited_at,
                    last_edited_by=classification_frame_instance_info.last_edited_by,
                    confidence=classification_frame_instance_info.confidence,
                    manual_annotation=classification_frame_instance_info.manual_annotation,
                    reviews=classification_frame_instance_info.reviews,
                )

    def _to_object_answers(self) -> dict[str, FrameObjectIndex]:
        ret: dict[str, FrameObjectIndex] = {}
        for obj in self.get_object_instances():
            all_static_answers = self.parent._get_all_static_answers(obj)
            object_index_element: FrameObjectIndex = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
            }
            ret[obj.object_hash] = object_index_element

        return ret

    def _to_classification_answers(self) -> dict[str, FrameClassificationIndex]:
        ret: dict[str, FrameClassificationIndex] = {}
        for classification in self.get_classification_instances():
            all_static_answers = classification.get_all_static_answers()
            classifications = [answer.to_encord_dict() for answer in all_static_answers if answer.is_answered()]
            classification_index_element: FrameClassificationIndex = {
                "classifications": classifications,
                "classificationHash": classification.classification_hash,
                "featureHash": classification.feature_hash,
            }

            ret[classification.classification_hash] = classification_index_element

        return ret
