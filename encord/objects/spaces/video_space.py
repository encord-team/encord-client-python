from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Set

from typing_extensions import Unpack

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects import Classification, ClassificationInstance
from encord.objects.common import Shape
from encord.objects.coordinates import (
    Coordinates,
    TwoDimensionalCoordinates,
    add_coordinates_to_frame_object_dict,
)
from encord.objects.frames import Frames, frames_class_to_frames_list
from encord.objects.label_utils import create_frame_classification_dict, create_frame_object_dict
from encord.objects.ontology_object_instance import (
    ObjectInstance,
)
from encord.objects.spaces.annotation.base_annotation import AnnotationData, AnnotationInfo
from encord.objects.spaces.annotation.video_annotation import (
    TwoDimensionalAnnotationData,
    TwoDimensionalFrameAnnotation,
)
from encord.objects.spaces.annotation_instance.base_instance import BaseObjectInstance
from encord.objects.spaces.annotation_instance.video_instance import VideoClassificationInstance, VideoObjectInstance
from encord.objects.spaces.base_space import Space
from encord.objects.spaces.entity import Entity
from encord.objects.spaces.types import AddObjectInstanceParams, FrameClassificationIndex, FrameObjectIndex
from encord.orm.label_space import LabelBlob, SpaceInfo, VideoSpaceInfo

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object


class VideoSpace(Space):
    """Video space implementation for frame-based video annotations."""

    def __init__(self, space_id: str, title: str, parent: LabelRowV2, number_of_frames: int, width: int, height: int):
        super().__init__(space_id, title, SpaceType.VIDEO, parent)
        self._objects_map: dict[str, VideoObjectInstance] = dict()
        self._classifications_map: dict[str, VideoClassificationInstance] = dict()
        self._frames_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        self._number_of_frames: int = number_of_frames
        self._width = width
        self._height = height
        self._frames_to_entity_hash_to_annotation_data: defaultdict[int, dict[str, TwoDimensionalAnnotationData]] = defaultdict(dict)
        self._frames_to_classification_hash_to_annotation_data: defaultdict[int, dict[str, AnnotationData]] = defaultdict(dict)
        self._object_entities_map: dict[str, Entity] = dict()
        self._classification_entities_map: dict[str, Entity] = dict()

    def _track_hash_for_frames(self, item_hash: str, frames: Iterable[int]) -> None:
        for frame in frames:
            self._frames_to_hashes[frame].add(item_hash)

    def _untrack_hash_for_frames(self, item_hash: str, frames: Iterable[int]) -> None:
        for frame in frames:
            self._frames_to_hashes[frame].discard(item_hash)

    def _get_tracked_frames_and_hashes(self) -> Iterable[tuple[int, Set[str]]]:
        return self._frames_to_hashes.items()

    def _add_object_instance(self, object_instance: VideoObjectInstance) -> VideoObjectInstance:
        """Add an object instance to this space and track it across its frames."""
        self._objects_map[object_instance.object_hash] = object_instance

        frames_list = [annotation.frame for annotation in object_instance.get_annotations()]
        self._track_hash_for_frames(object_instance.object_hash, frames_list)

        return object_instance

    def _create_new_entity_from_frame_label_dict(self, frame_object_label: dict) -> Entity:
        from encord.objects.ontology_object import Object

        ontology = self.parent._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)

        entity = self.parent.create_entity(ontology_class=label_class, entity_hash=object_hash)

        return entity

    def _create_new_classification_entity_from_frame_label_dict(self, frame_classification_label: dict, classification_answers: dict) -> Optional[Entity]:
        ontology = self.parent._ontology.structure
        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Classification)
        
        if classification_answer := classification_answers.get(classification_hash):
            entity = self.parent.create_entity(ontology_class=label_class, entity_hash=classification_hash)
            answers_dict = classification_answer["classifications"]
            self.parent._add_static_answers_from_dict(entity._entity_instance, answers_dict)
            return entity

        return None





        return entity

    def _add_classification_instance(self, classification_instance: VideoClassificationInstance) -> None:
        """Add an object instance to this space and track it across its frames."""
        self._classifications_map[classification_instance.classification_hash] = classification_instance

        frames_list = classification_instance.get_annotation_frames()
        self._track_hash_for_frames(classification_instance.classification_hash, frames_list)

    def _create_new_classification_instance_from_frame_label_dict(
        self, frame_classification_label: dict, frame: int, classification_answers: dict
    ):
        from encord.objects.classification import Classification

        feature_hash = frame_classification_label["featureHash"]
        classification_hash = frame_classification_label["classificationHash"]

        label_class = self.parent._ontology.structure.get_child_by_hash(feature_hash, type_=Classification)
        classification_instance = VideoClassificationInstance(
            label_class, classification_hash=classification_hash, space=self
        )

        frame_view = ClassificationInstance.FrameData.from_dict(frame_classification_label)
        classification_instance.set_annotation_for_frames(
            frame,
            created_at=frame_view.created_at,
            created_by=frame_view.created_by,
            confidence=frame_view.confidence,
            manual_annotation=frame_view.manual_annotation,
            last_edited_at=frame_view.last_edited_at,
            last_edited_by=frame_view.last_edited_by,
            reviews=frame_view.reviews,
            overwrite=True,  # Always overwrite during label row dict parsing, as older dicts known to have duplicates
        )

        # For some older label rows we might have a classification entry, but without an assigned answer.
        # These cases are equivalent to not having classifications at all, so just ignoring them
        if classification_answer := classification_answers.get(classification_hash):
            answers_dict = classification_answer["classifications"]
            classification_instance.set_answer_from_list(answers_dict)
            return classification_instance

        return None

    def add_object_instance(
        self,
        obj: Object,
        coordinates: TwoDimensionalCoordinates,
        frames: Frames = 0,
        **kwargs: Unpack[AddObjectInstanceParams],
    ) -> VideoObjectInstance:
        """Add an object instance to the video space."""
        object_instance = VideoObjectInstance(obj, space=self)
        object_instance.add_annotation(coordinates=coordinates, frames=frames, overwrite=False, **kwargs)
        self._add_object_instance(object_instance)

        return object_instance

    def get_object_instances(self) -> list[VideoObjectInstance]:
        """Get all object instances in this space."""
        return list(self._objects_map.values())

    def add_classification_instance(
        self, classification: Classification, frames: Frames = 0, **kwargs: Unpack[AddObjectInstanceParams]
    ) -> VideoClassificationInstance:
        """Add a classification instance to the video space."""
        classification_instance = VideoClassificationInstance(ontology_classification=classification, space=self)
        classification_instance.set_annotation_for_frames(frames=frames, overwrite=False, **kwargs)
        self._add_classification_instance(classification_instance)

        return classification_instance

    def remove_object_instance(self, object_hash: str) -> Optional[VideoObjectInstance]:
        """Remove an object instance from this space by its hash."""
        removed_object_instance = self._objects_map.pop(object_hash, None)

        if removed_object_instance is None:
            return None
        else:
            removed_object_instance._set_space(None)
            frame_list = removed_object_instance.get_annotation_frames()

            self._untrack_hash_for_frames(object_hash, frame_list)

        return removed_object_instance

    def move_object_instance_from_space(self, object_to_move: VideoObjectInstance) -> None:
        """Move an object instance from another space to this space."""
        original_space = object_to_move._space

        if original_space is None:
            raise LabelRowError("Unable to move object instance, as it currently does not belong to any space.")

        original_space.remove_object_instance(object_to_move.object_hash)
        self._add_object_instance(object_to_move)

    def get_classification_instances(self) -> list[VideoClassificationInstance]:
        """Get all classification instances in this space."""
        return list(self._classifications_map.values())

    def remove_classification_instance(self, classification_hash: str) -> Optional[VideoClassificationInstance]:
        """Remove a classification instance from this space by its hash."""
        removed_classification_instance = self._classifications_map.pop(classification_hash, None)

        if removed_classification_instance is None:
            return None
        else:
            removed_classification_instance._set_space(None)
            frame_list = removed_classification_instance.get_annotation_frames()
            self._untrack_hash_for_frames(classification_hash, frame_list)

        return removed_classification_instance

    def move_classification_instance_from_space(self, classification_to_move: VideoClassificationInstance) -> None:
        """Move a classification instance from another space to this space."""
        original_space = classification_to_move._space

        if original_space is None:
            raise LabelRowError("Unable to move classification instance, as it currently does not belong to any space.")

        original_space.remove_classification_instance(classification_to_move.classification_hash)
        self._add_classification_instance(classification_to_move)

    def _get_frame_object_annotation_data(self, entity_hash: str, frame: int) -> Optional[TwoDimensionalAnnotationData]:
        entity_to_frame_annotation_data = self._frames_to_entity_hash_to_annotation_data.get(frame)
        if entity_to_frame_annotation_data is None:
            return None
        else:
            return entity_to_frame_annotation_data.get(entity_hash)

    def _get_frame_classification_annotation_data(self, classification_hash: str, frame: int) -> Optional[AnnotationData]:
        classification_to_frame_annotation_data = self._frames_to_classification_hash_to_annotation_data.get(frame)
        if classification_to_frame_annotation_data is None:
            return None
        else:
            return classification_to_frame_annotation_data.get(classification_hash)

    def place_object_entity(
        self,
        entity: Entity,
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
        self._object_entities_map[entity.entity_hash] = entity

        # TODO: Check overwrites

        for frame in frame_list:
            existing_frame_annotation_data = self._get_frame_object_annotation_data(entity_hash=entity.entity_hash, frame=frame)
            if existing_frame_annotation_data is None:
                existing_frame_annotation_data = TwoDimensionalAnnotationData(
                    object_frame_instance_info=AnnotationInfo(),
                    coordinates=coordinates,
                )

                self._frames_to_entity_hash_to_annotation_data[frame][entity.entity_hash] = existing_frame_annotation_data

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
        entity: Entity,
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
        self._classification_entities_map[entity.entity_hash] = entity

        # TODO: Check overwrites

        for frame in frame_list:
            existing_frame_classification_annotation_data = self._get_frame_classification_annotation_data(classification_hash=entity.entity_hash, frame=frame)
            if existing_frame_classification_annotation_data is None:
                existing_frame_classification_annotation_data = AnnotationData(
                    object_frame_instance_info=AnnotationInfo(),
                )

                self._frames_to_classification_hash_to_annotation_data[frame][entity.entity_hash] = existing_frame_classification_annotation_data

            existing_frame_classification_annotation_data.object_frame_instance_info.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                reviews=reviews,
                is_deleted=is_deleted,
            )

    def get_object_annotations(self) -> list[TwoDimensionalFrameAnnotation]:
        res: list[TwoDimensionalFrameAnnotation] = []

        for frame, obj in dict(sorted(self._frames_to_entity_hash_to_annotation_data.items())).items():
            for obj_hash, annotation in obj.items():
                res.append(TwoDimensionalFrameAnnotation(space=self, entity=self._object_entities_map[obj_hash], frame=frame))

        return res

    def get_classification_annotations(self) -> list[TwoDimensionalFrameAnnotation]:
        res: list[TwoDimensionalFrameAnnotation] = []

        for frame, classification in dict(sorted(self._frames_to_classification_hash_to_annotation_data.items())).items():
            for classification_hash, annotation in classification.items():
                res.append(TwoDimensionalFrameAnnotation(space=self, entity=self._classification_entities_map[classification_hash], frame=frame))

        return res

    def get_object_entities(self) -> list[Entity]:
        return list(self._object_entities_map.values())

    def get_classification_entities(self) -> list[Entity]:
        return list(self._classification_entities_map.values())

    def remove_entity(self, entity_hash: str) -> Optional[ObjectInstance]:
        self._object_entities_map.pop(entity_hash, None)
        for frame, obj in self._frames_to_entity_hash_to_annotation_data.items():
            if entity_hash in obj:
                obj.pop(entity_hash)

    """INTERNAL METHODS FOR DESERDE"""

    def _to_encord_object(
        self,
        object_entity: Entity,
        frame_object_annotation_data: TwoDimensionalAnnotationData,
    ) -> Dict[str, Any]:
        from encord.objects.ontology_object import Object

        ontology_hash = object_entity._entity_instance._ontology_object.feature_node_hash
        ontology_object = self.parent._ontology.structure.get_child_by_hash(ontology_hash, type_=Object)

        frame_object_dict = create_frame_object_dict(
            ontology_object=ontology_object,
            object_hash=object_entity.entity_hash,
            object_instance_annotation=frame_object_annotation_data.object_frame_instance_info,
        )

        add_coordinates_to_frame_object_dict(
            coordinates=frame_object_annotation_data.coordinates, frame_object_dict=frame_object_dict, width=self._width, height=self._height
        )

        return frame_object_dict

    def _to_encord_classification(
        self,
        classification_entity: Entity,
        frame_classification_annotation_data: AnnotationData,
    ) -> Dict[str, Any]:
        from encord.objects import Classification
        from encord.objects.attributes import Attribute

        ontology_hash = classification_entity._entity_instance._ontology_classification.feature_node_hash
        ontology_classification = self.parent._ontology.structure.get_child_by_hash(ontology_hash, type_=Classification)

        attribute_hash = classification_entity._entity_instance.ontology_item.attributes[0].feature_node_hash
        attribute = self.parent._ontology.structure.get_child_by_hash(attribute_hash, type_=Attribute)

        frame_object_dict = create_frame_classification_dict(
            ontology_classification=ontology_classification,
            classification_instance_annotation=frame_classification_annotation_data.object_frame_instance_info,
            classification_hash=classification_entity.entity_hash,
            attribute=attribute,
        )

        return frame_object_dict

    def _build_frame_label_dict(self, frame: int) -> LabelBlob:
        object_list = []
        classification_list = []

        objects_to_annotation_data = self._frames_to_entity_hash_to_annotation_data.get(frame, {})
        classifications_to_annotation_data = self._frames_to_classification_hash_to_annotation_data.get(frame, {})

        for object_hash, frame_object_annotation_data in objects_to_annotation_data.items():
            entity = self._object_entities_map[object_hash]
            object_list.append(self._to_encord_object(object_entity=entity, frame_object_annotation_data=frame_object_annotation_data))

        for classification_hash, frame_classification_annotation_data in classifications_to_annotation_data.items():
            entity = self._classification_entities_map[classification_hash]
            classification_list.append(self._to_encord_classification(classification_entity=entity, frame_classification_annotation_data=frame_classification_annotation_data))

        return LabelBlob(
            objects=object_list,
            classifications=classification_list,
        )

    def _to_object_answers(self) -> dict[str, FrameObjectIndex]:
        ret: dict[str, FrameObjectIndex] = {}
        for obj in self._object_entities_map.values():
            all_static_answers = self.parent._get_all_static_answers(obj._entity_instance)
            object_index_element: FrameObjectIndex = {
                "classifications": list(reversed(all_static_answers)),
                "objectHash": obj.entity_hash,
            }
            ret[obj.entity_hash] = object_index_element

        return ret

    def _to_classification_answers(self) -> dict[str, FrameClassificationIndex]:
        ret: dict[str, FrameClassificationIndex] = {}
        for classification_entity in self._classification_entities_map.values():
            classification = classification_entity._entity_instance
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
            entity = self.parent._entities_map.get(object_hash)
            if entity is None:
                entity = self._create_new_entity_from_frame_label_dict(frame_object_label=obj)

            coordinates = self.parent._get_coordinates(obj)
            object_frame_instance_info = AnnotationInfo.from_dict(obj)
            self.place_object_entity(
                entity=entity,
                coordinates=coordinates,
                frames=frame,
                created_at=object_frame_instance_info.created_at,
                created_by=object_frame_instance_info.created_by,
                last_edited_at=object_frame_instance_info.last_edited_at,
                last_edited_by=object_frame_instance_info.last_edited_by,
                manual_annotation=object_frame_instance_info.manual_annotation,
                reviews=object_frame_instance_info.reviews,
                confidence=object_frame_instance_info.confidence,
                is_deleted=object_frame_instance_info.is_deleted,
            )

        # Process classifications
        for classification in frame_label["classifications"]:
            classification_hash = classification["classificationHash"]
            entity = self.parent._entities_map.get(classification_hash)

            if entity is None:
                entity = self._create_new_classification_entity_from_frame_label_dict(
                    frame_classification_label=classification,
                    classification_answers=classification_answers
                )

            if entity is None:
                continue

            classification_frame_instance_info = AnnotationInfo.from_dict(classification)
            self.place_classification_entity(
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

        for frame, object_hash_to_annotation_data in self._frames_to_entity_hash_to_annotation_data.items():
            frame_label = self._build_frame_label_dict(frame=frame)
            labels[str(frame)] = frame_label

        return VideoSpaceInfo(
            space_type=self.space_type,
            labels=labels,
            number_of_frames=self._number_of_frames,
            width=self._width,
            height=self._height,
        )


class SceneStreamSpace(Space):
    def __init__(self, space_id: str, title: str, parent: LabelRowV2):
        super().__init__(space_id, title, SpaceType.SCENE_STREAM, parent)

    def get_object_instances(
        self,
        filter_ontology_object: Optional[Object] = None,
    ) -> list[ObjectInstance]:
        raise NotImplementedError()

    def add_object_instance(self, obj: Object, coordinates: Coordinates) -> ObjectInstance:
        if obj.shape != Shape.SEGMENTATION:
            raise ValueError(f"Only segmentation spaces are allowed on SceneStreamSpace.")

        object_instance = obj.create_instance()
        # For Point Cloud, no frames, it applies to whole file
        object_instance.set_for_frames(coordinates=coordinates)
        self.parent.add_object_instance(object_instance=object_instance)
        return object_instance
