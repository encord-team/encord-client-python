from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from encord.constants.enums import SpaceType
from encord.objects import Classification
from encord.objects.coordinates import (
    TwoDimensionalCoordinates,
    add_coordinates_to_frame_object_dict,
)
from encord.objects.frames import Frames, frames_class_to_frames_list
from encord.objects.label_utils import create_frame_classification_dict, create_frame_object_dict
from encord.objects.spaces.annotation.base_annotation import AnnotationData, AnnotationInfo
from encord.objects.spaces.annotation.two_dimensional_annotation import (
    FrameClassificationAnnotation,
    TwoDimensionalAnnotationData,
    TwoDimensionalFrameObjectAnnotation,
)
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.space_entity import SpaceClassification, SpaceObject
from encord.objects.spaces.types import FrameClassificationIndex, FrameObjectIndex
from encord.orm.label_space import LabelBlob, SpaceInfo, VideoSpaceInfo

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object


class VideoSpace(Space):
    """Video space implementation for frame-based video annotations."""

    def __init__(self, space_id: str, title: str, parent: LabelRowV2, number_of_frames: int, width: int, height: int):
        super().__init__(space_id, title, SpaceType.VIDEO, parent)
        self._frames_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        self._number_of_frames: int = number_of_frames
        self._width = width
        self._height = height
        self._frames_to_object_hash_to_annotation_data: defaultdict[int, dict[str, TwoDimensionalAnnotationData]] = (
            defaultdict(dict)
        )
        self._frames_to_classification_hash_to_annotation_data: defaultdict[int, dict[str, AnnotationData]] = (
            defaultdict(dict)
        )
        self._objects_map: dict[str, SpaceObject] = dict()
        self._classification_map: dict[str, SpaceClassification] = dict()

    def place_object(
        self,
        object: SpaceObject,
        frames: Frames,
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
        frame_list = frames_class_to_frames_list(frames)
        self._objects_map[object.object_hash] = object
        object._space_ids.add(self.space_id)

        # TODO: Check overwrites

        for frame in frame_list:
            existing_frame_annotation_data = self._get_frame_object_annotation_data(
                object_hash=object.object_hash, frame=frame
            )
            if existing_frame_annotation_data is None:
                existing_frame_annotation_data = TwoDimensionalAnnotationData(
                    annotation_info=AnnotationInfo(),
                    coordinates=coordinates,
                )

                self._frames_to_object_hash_to_annotation_data[frame][object.object_hash] = (
                    existing_frame_annotation_data
                )

            existing_frame_annotation_data.annotation_info.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                reviews=reviews,
                is_deleted=is_deleted,
            )

    def place_classification(
        self,
        classification: SpaceClassification,
        frames: Frames,
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
        frame_list = frames_class_to_frames_list(frames)
        self._classification_map[classification.classification_hash] = classification
        classification._space_ids.add(self.space_id)

        # TODO: Check overwrites

        for frame in frame_list:
            existing_frame_classification_annotation_data = self._get_frame_classification_annotation_data(
                classification_hash=classification.classification_hash, frame=frame
            )
            if existing_frame_classification_annotation_data is None:
                existing_frame_classification_annotation_data = AnnotationData(
                    annotation_info=AnnotationInfo(),
                )

                self._frames_to_classification_hash_to_annotation_data[frame][classification.classification_hash] = (
                    existing_frame_classification_annotation_data
                )

            existing_frame_classification_annotation_data.annotation_info.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                reviews=reviews,
                is_deleted=is_deleted,
            )

    def get_object_annotations(self) -> list[TwoDimensionalFrameObjectAnnotation]:
        res: list[TwoDimensionalFrameObjectAnnotation] = []

        for frame, obj in dict(sorted(self._frames_to_object_hash_to_annotation_data.items())).items():
            for obj_hash, annotation in obj.items():
                res.append(
                    TwoDimensionalFrameObjectAnnotation(
                        space=self, object_instance=self._objects_map[obj_hash], frame=frame
                    )
                )

        return res

    def get_classification_annotations(self) -> list[FrameClassificationAnnotation]:
        res: list[FrameClassificationAnnotation] = []

        for frame, classification in dict(
            sorted(self._frames_to_classification_hash_to_annotation_data.items())
        ).items():
            for classification_hash, annotation in classification.items():
                res.append(
                    FrameClassificationAnnotation(
                        space=self, classification_instance=self._classification_map[classification_hash], frame=frame
                    )
                )

        return res

    def get_objects(self) -> list[SpaceObject]:
        return list(self._objects_map.values())

    def get_classifications(self) -> list[SpaceClassification]:
        return list(self._classification_map.values())

    def remove_space_object(self, object_hash: str) -> Optional[SpaceObject]:
        obj_entity = self._objects_map.pop(object_hash, None)
        for frame, obj in self._frames_to_object_hash_to_annotation_data.items():
            if object_hash in obj:
                obj.pop(object_hash)

        return obj_entity

    def remove_space_classification(self, classification_hash: str) -> Optional[SpaceClassification]:
        classification_entity = self._classification_map.pop(classification_hash, None)
        for frame, classification in self._frames_to_classification_hash_to_annotation_data.items():
            if classification_hash in classification:
                classification.pop(classification_hash)

        return classification_entity

    """INTERNAL METHODS FOR DESERDE"""

    def _create_new_space_object_from_frame_label_dict(self, frame_object_label: dict) -> SpaceObject:
        from encord.objects.ontology_object import Object

        ontology = self.parent._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)

        entity = self.parent.create_space_object(ontology_class=label_class, entity_hash=object_hash)

        return entity

    def _create_new_classification_from_frame_label_dict(
        self, frame_classification_label: dict, classification_answers: dict
    ) -> Optional[SpaceClassification]:
        ontology = self.parent._ontology.structure
        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Classification)

        # TODO: Probably can remove this check?
        if classification_answer := classification_answers.get(classification_hash):
            entity = self.parent.create_space_classification(
                ontology_class=label_class, entity_hash=classification_hash
            )
            answers_dict = classification_answer["classifications"]
            self.parent._add_static_answers_from_dict(entity._classification_instance, answers_dict)

            return entity

        return None

    def _get_frame_object_annotation_data(self, object_hash: str, frame: int) -> Optional[TwoDimensionalAnnotationData]:
        entity_to_frame_annotation_data = self._frames_to_object_hash_to_annotation_data.get(frame)
        if entity_to_frame_annotation_data is None:
            return None
        else:
            return entity_to_frame_annotation_data.get(object_hash)

    def _get_frame_classification_annotation_data(
        self, classification_hash: str, frame: int
    ) -> Optional[AnnotationData]:
        classification_to_frame_annotation_data = self._frames_to_classification_hash_to_annotation_data.get(frame)
        if classification_to_frame_annotation_data is None:
            return None
        else:
            return classification_to_frame_annotation_data.get(classification_hash)

    def _to_encord_object(
        self,
        space_object: SpaceObject,
        frame_object_annotation_data: TwoDimensionalAnnotationData,
    ) -> Dict[str, Any]:
        from encord.objects.ontology_object import Object

        ontology_hash = space_object._object_instance._ontology_object.feature_node_hash
        ontology_object = self.parent._ontology.structure.get_child_by_hash(ontology_hash, type_=Object)

        frame_object_dict = create_frame_object_dict(
            ontology_object=ontology_object,
            object_hash=space_object.object_hash,
            object_instance_annotation=frame_object_annotation_data.annotation_info,
        )

        add_coordinates_to_frame_object_dict(
            coordinates=frame_object_annotation_data.coordinates,
            frame_object_dict=frame_object_dict,
            width=self._width,
            height=self._height,
        )

        return frame_object_dict

    def _to_encord_classification(
        self,
        space_classification: SpaceClassification,
        frame_classification_annotation_data: AnnotationData,
    ) -> Dict[str, Any]:
        from encord.objects import Classification
        from encord.objects.attributes import Attribute

        ontology_hash = space_classification._classification_instance._ontology_classification.feature_node_hash
        ontology_classification = self.parent._ontology.structure.get_child_by_hash(ontology_hash, type_=Classification)

        attribute_hash = space_classification._classification_instance.ontology_item.attributes[0].feature_node_hash
        attribute = self.parent._ontology.structure.get_child_by_hash(attribute_hash, type_=Attribute)

        frame_object_dict = create_frame_classification_dict(
            ontology_classification=ontology_classification,
            classification_instance_annotation=frame_classification_annotation_data.annotation_info,
            classification_hash=space_classification.classification_hash,
            attribute=attribute,
        )

        return frame_object_dict

    def _build_frame_label_dict(self, frame: int) -> LabelBlob:
        object_list = []
        classification_list = []

        objects_to_annotation_data = self._frames_to_object_hash_to_annotation_data.get(frame, {})
        classifications_to_annotation_data = self._frames_to_classification_hash_to_annotation_data.get(frame, {})

        for object_hash, frame_object_annotation_data in objects_to_annotation_data.items():
            space_object = self._objects_map[object_hash]
            object_list.append(
                self._to_encord_object(
                    space_object=space_object, frame_object_annotation_data=frame_object_annotation_data
                )
            )

        for classification_hash, frame_classification_annotation_data in classifications_to_annotation_data.items():
            space_classification = self._classification_map[classification_hash]
            classification_list.append(
                self._to_encord_classification(
                    space_classification=space_classification,
                    frame_classification_annotation_data=frame_classification_annotation_data,
                )
            )

        return LabelBlob(
            objects=object_list,
            classifications=classification_list,
        )

    def _to_object_answers(self) -> dict[str, FrameObjectIndex]:
        ret: dict[str, FrameObjectIndex] = {}
        for obj in self._objects_map.values():
            all_static_answers = self.parent._get_all_static_answers(obj._object_instance)
            object_index_element: FrameObjectIndex = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": obj.object_hash,
            }
            ret[obj.object_hash] = object_index_element

        return ret

    def _to_classification_answers(self) -> dict[str, FrameClassificationIndex]:
        ret: dict[str, FrameClassificationIndex] = {}
        for classification_entity in self._classification_map.values():
            classification = classification_entity._classification_instance
            all_static_answers = classification.get_all_static_answers()
            classifications = [answer.to_encord_dict() for answer in all_static_answers if answer.is_answered()]
            classification_index_element: FrameClassificationIndex = {
                "classifications": classifications,
                "classificationHash": classification.classification_hash,
                "featureHash": classification.feature_hash,
            }

            ret[classification.classification_hash] = classification_index_element

        return ret

    def _parse_space_dict(self, space_info: SpaceInfo, object_answers: dict, classification_answers: dict) -> None:
        for frame_str, frame_label in space_info["labels"].items():
            self._parse_frame_label_dict(
                frame=int(frame_str), frame_label=frame_label, classification_answers=classification_answers
            )

    def _parse_frame_label_dict(self, frame: int, frame_label: dict, classification_answers: dict):
        for obj in frame_label["objects"]:
            object_hash = obj["objectHash"]
            object = self.parent._space_objects_map.get(object_hash)
            if object is None:
                object = self._create_new_space_object_from_frame_label_dict(frame_object_label=obj)

            coordinates = self.parent._get_coordinates(obj)
            object_frame_instance_info = AnnotationInfo.from_dict(obj)
            self.place_object(
                object=object,
                coordinates=coordinates,
                frames=frame,
                created_at=object_frame_instance_info.created_at,
                created_by=object_frame_instance_info.created_by,
                last_edited_at=object_frame_instance_info.last_edited_at,
                last_edited_by=object_frame_instance_info.last_edited_by,
                manual_annotation=object_frame_instance_info.manual_annotation,
                reviews=object_frame_instance_info.reviews,
                confidence=object_frame_instance_info.confidence,
                # is_deleted=object_frame_instance_info.is_deleted,
            )

        # Process classifications
        for classification in frame_label["classifications"]:
            classification_hash = classification["classificationHash"]
            entity = self.parent._space_classifications_map.get(classification_hash)

            if entity is None:
                entity = self._create_new_classification_from_frame_label_dict(
                    frame_classification_label=classification, classification_answers=classification_answers
                )

            if entity is None:
                continue

            classification_frame_instance_info = AnnotationInfo.from_dict(classification)
            self.place_classification(
                entity,
                frames=frame,
                created_at=classification_frame_instance_info.created_at,
                created_by=classification_frame_instance_info.created_by,
                last_edited_at=classification_frame_instance_info.last_edited_at,
                last_edited_by=classification_frame_instance_info.last_edited_by,
                manual_annotation=classification_frame_instance_info.manual_annotation,
                reviews=classification_frame_instance_info.reviews,
                confidence=classification_frame_instance_info.confidence,
            )

    def _to_space_dict(self) -> VideoSpaceInfo:
        """Export video space to dictionary format."""
        labels: dict[str, LabelBlob] = {}

        for frame, object_hash_to_annotation_data in self._frames_to_object_hash_to_annotation_data.items():
            frame_label = self._build_frame_label_dict(frame=frame)
            labels[str(frame)] = frame_label

        return VideoSpaceInfo(
            space_type=self.space_type,
            labels=labels,
            number_of_frames=self._number_of_frames,
            width=self._width,
            height=self._height,
        )
