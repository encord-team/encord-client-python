from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Set

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
from encord.objects.frames import Frames
from encord.objects.label_utils import create_frame_object_dict
from encord.objects.ontology_object_instance import (
    ObjectInstance,
)
from encord.objects.spaces.annotation_instance.base_instance import BaseObjectInstance
from encord.objects.spaces.annotation_instance.video_instance import VideoClassificationInstance, VideoObjectInstance
from encord.objects.spaces.base_space import Space
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

    def _create_new_object_instance_from_frame_label_dict(self, frame_object_label: dict, frame: int):
        from encord.objects.ontology_object import Object

        ontology = self.parent._ontology.structure
        feature_hash = frame_object_label["featureHash"]
        object_hash = frame_object_label["objectHash"]
        label_class = ontology.get_child_by_hash(feature_hash, type_=Object)

        object_instance = VideoObjectInstance(label_class, object_hash=object_hash, space=self)

        coordinates = self.parent._get_coordinates(frame_object_label)
        object_frame_instance_info = BaseObjectInstance.AnnotationInfo.from_dict(frame_object_label)
        object_instance.add_annotation(
            coordinates=coordinates,
            frames=frame,
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

    """INTERNAL METHODS FOR DESERDE"""

    def _to_encord_object(
        self,
        object_: VideoObjectInstance,
        frame: int,
    ) -> Dict[str, Any]:
        from encord.objects.ontology_object import Object

        object_instance_annotation = object_.get_annotation(frame)

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

    def _build_frame_label_dict(self, frame: int, label_hashes: set[str]) -> LabelBlob:
        object_list = []
        classification_list = []

        for label_hash in label_hashes:
            frame_object_instance = self._objects_map.get(label_hash)
            frame_classification_instance = self._classifications_map.get(label_hash)

            if frame_object_instance is None and frame_classification_instance is None:
                continue
            elif frame_object_instance is not None:
                object_list.append(self._to_encord_object(frame_object_instance, frame))
            else:
                classification_list.append(self.parent._to_encord_classification(frame_classification_instance, frame))

        return LabelBlob(
            objects=object_list,
            classifications=classification_list,
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

    def _parse_space_dict(self, space_info: SpaceInfo, object_answers: dict, classification_answers: dict) -> None:
        for frame_str, frame_label in space_info["labels"].items():
            self._parse_frame_label_dict(
                frame=int(frame_str), frame_label=frame_label, classification_answers=classification_answers
            )

    def _parse_frame_label_dict(self, frame: int, frame_label: dict, classification_answers: dict):
        for obj in frame_label["objects"]:
            object_hash = obj["objectHash"]
            if object_hash not in self._objects_map:
                new_object_instance = self._create_new_object_instance_from_frame_label_dict(obj, frame)
                self._add_object_instance(new_object_instance)
            else:
                object_instance = self._objects_map[object_hash]
                coordinates = self.parent._get_coordinates(obj)
                object_frame_instance_info = BaseObjectInstance.AnnotationInfo.from_dict(obj)

                object_instance.add_annotation(
                    coordinates=coordinates,
                    frames=frame,
                    created_at=object_frame_instance_info.created_at,
                    created_by=object_frame_instance_info.created_by,
                    last_edited_at=object_frame_instance_info.last_edited_at,
                    last_edited_by=object_frame_instance_info.last_edited_by,
                    confidence=object_frame_instance_info.confidence,
                    manual_annotation=object_frame_instance_info.manual_annotation,
                    reviews=object_frame_instance_info.reviews,
                    is_deleted=object_frame_instance_info.is_deleted,
                )

        # Process classifications
        for classification in frame_label["classifications"]:
            classification_hash = classification["classificationHash"]
            if classification_hash not in self._classifications_map:
                new_classification_instance = self._create_new_classification_instance_from_frame_label_dict(
                    classification, frame, classification_answers
                )
                self._add_classification_instance(new_classification_instance)
            else:
                classification_instance = self._classifications_map[classification_hash]
                classification_frame_instance_info = ClassificationInstance.FrameData.from_dict(classification)

                classification_instance.set_for_frames(
                    frames=frame,
                    created_at=classification_frame_instance_info.created_at,
                    created_by=classification_frame_instance_info.created_by,
                    last_edited_at=classification_frame_instance_info.last_edited_at,
                    last_edited_by=classification_frame_instance_info.last_edited_by,
                    confidence=classification_frame_instance_info.confidence,
                    manual_annotation=classification_frame_instance_info.manual_annotation,
                    reviews=classification_frame_instance_info.reviews,
                )

    def _to_space_dict(self) -> VideoSpaceInfo:
        """Export video space to dictionary format."""
        labels: dict[str, LabelBlob] = {}

        for frame, label_hashes in self._frames_to_hashes.items():
            frame_label = self._build_frame_label_dict(frame=frame, label_hashes=label_hashes)
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
