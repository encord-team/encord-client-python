from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Set, Any, TypedDict

from typing_extensions import Unpack

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects import Classification, ClassificationInstance
from encord.objects.common import Shape
from encord.objects.coordinates import Coordinates, TwoDimensionalCoordinates
from encord.objects.frames import Frames
from encord.objects.ontology_object_instance import ObjectInstance, SetFramesKwargs
from encord.objects.spaces.base_space import Space
from encord.orm.label_space import BaseSpaceInfo, ImageSpaceInfo, LabelBlob, SpaceInfo, VideoSpaceInfo

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.ontology_object import Object

class FrameAnnotationIndex(TypedDict):
    classifications: list[dict[str, Any]]

class FrameClassificationIndex(FrameAnnotationIndex):
    classificationHash: str
    featureHash: str

class FrameObjectIndex(FrameAnnotationIndex):
    objectHash: str

# TODO: Use this for DICOM/NIfTI
class FrameBasedSpace(Space, ABC):
    """Abstract base class for spaces that manage frame-based annotations (Video and Image).

    This class extracts common logic for managing object and classification instances
    across frames, with concrete implementations handling frame tracking differently.
    """

    def __init__(self, space_id: str, title: str, space_type: SpaceType, parent: LabelRowV2):
        super().__init__(space_id, title, space_type, parent)
        self._objects_map: Dict[str, ObjectInstance] = dict()
        self._classifications_map: Dict[str, ClassificationInstance] = dict()

    @abstractmethod
    def _track_hash_for_frames(self, item_hash: str, frames: Iterable[int]) -> None:
        """Track a label hash (object or classification) for the given frames.

        Args:
            item_hash: The object_hash or classification_hash to track
            frames: Iterable of frame numbers where this hash exists
        """
        pass

    @abstractmethod
    def _untrack_hash_for_frames(self, item_hash: str, frames: Iterable[int]) -> None:
        """Untrack a label hash (object or classification) from the given frames.

        Args:
            item_hash: The object_hash or classification_hash to untrack
            frames: Iterable of frame numbers to remove this hash from
        """
        pass

    @abstractmethod
    def _get_frames_to_process(self, space_info: BaseSpaceInfo) -> Iterable[tuple[int, LabelBlob]]:
        """Get frames and their label data to process during parsing.

        Args:
            space_info: The space information to extract frames from

        Returns:
            Iterable of (frame_number, label_blob) tuples
        """
        pass

    @abstractmethod
    def _get_tracked_frames_and_hashes(self) -> Iterable[tuple[int, Set[str]]]:
        """Get all tracked frames and their associated hashes for export.

        Returns:
            Iterable of (frame_number, set_of_hashes) tuples
        """
        pass

    def _add_object_instance(self, object_instance: ObjectInstance) -> ObjectInstance:
        """Add an object instance to this space and track it across its frames."""
        self._objects_map[object_instance.object_hash] = object_instance
        object_instance._set_space(self)

        frames_list = object_instance.get_annotation_frames()
        self._track_hash_for_frames(object_instance.object_hash, frames_list)

        return object_instance

    def _add_classification_instance(self, classification_instance: ClassificationInstance) -> ClassificationInstance:
        """Add a classification instance to this space and track it across its frames."""
        self._classifications_map[classification_instance.classification_hash] = classification_instance
        classification_instance._set_space(self)

        frames_list = classification_instance.get_annotation_frames()
        self._track_hash_for_frames(classification_instance.classification_hash, frames_list)

        return classification_instance

    def _add_to_single_frame_to_hashes_map(self, label: ObjectInstance, frame: int) -> None:
        """Track a label on a single frame (called when coordinates are set on existing instances)."""
        if isinstance(label, ObjectInstance):
            self._track_hash_for_frames(label.object_hash, [frame])

    def get_object_instances(self) -> list[ObjectInstance]:
        """Get all object instances in this space."""
        return list(self._objects_map.values())

    def get_classification_instances(self) -> list[ClassificationInstance]:
        """Get all classification instances in this space."""
        return list(self._classifications_map.values())

    def remove_object_instance(self, object_hash: str) -> Optional[ObjectInstance]:
        """Remove an object instance from this space by its hash."""
        object_instance = self._objects_map.pop(object_hash, None)

        if object_instance is None:
            logger.warning(f"Object instance {object_hash} not found.")
        else:
            object_instance_frame_list = object_instance.get_annotation_frames()
            self._untrack_hash_for_frames(object_hash, object_instance_frame_list)
            object_instance._set_space(None)

        return object_instance

    def remove_classification_instance(self, classification_hash: str) -> Optional[ClassificationInstance]:
        """Remove a classification instance from this space by its hash."""
        classification_instance = self._classifications_map.pop(classification_hash, None)

        if classification_instance is None:
            logger.warning(f"Classification instance {classification_hash} not found.")
        else:
            classification_instance_frame_list = classification_instance.get_annotation_frames()
            self._untrack_hash_for_frames(classification_hash, classification_instance_frame_list)
            classification_instance._set_space(None)

        return classification_instance

    def move_object_instance_from_space(self, object_to_move: ObjectInstance) -> Optional[ObjectInstance]:
        """Move an object instance from another space to this space."""
        original_space = object_to_move._space

        if original_space is None:
            raise LabelRowError("Unable to move object instance, as it currently does not belong to any space.")

        if isinstance(original_space, FrameBasedSpace):
            original_space.remove_object_instance(object_to_move.object_hash)
            self._add_object_instance(object_to_move)
            return object_to_move
        else:
            logger.warning(
                f"Unable to move object instance from space of type {original_space.space_type} to {self.space_type}"
            )
            return None

    def move_classification_instance_from_space(
        self, classification_to_move: ClassificationInstance
    ) -> Optional[ClassificationInstance]:
        """Move a classification instance from another space to this space."""
        original_space = classification_to_move._space

        if original_space is None:
            raise LabelRowError("Unable to move classification instance, as it currently does not belong to any space.")

        if isinstance(original_space, FrameBasedSpace):
            original_space.remove_classification_instance(classification_to_move.classification_hash)
            self._add_classification_instance(classification_to_move)
            return classification_to_move
        else:
            logger.warning(
                f"Unable to move classification instance from space of type {original_space.space_type} to {self.space_type}"
            )
            return None

    def _parse_space_dict(self, space_info: BaseSpaceInfo, object_answers: dict, classification_answers: dict) -> None:
        """Parse space dictionary and populate object and classification instances."""
        for frame, frame_label in self._get_frames_to_process(space_info):
            # Process objects
            for obj in frame_label["objects"]:
                object_hash = obj["objectHash"]
                if object_hash not in self._objects_map:
                    new_object_instance = self.parent._create_new_object_instance(obj, frame)
                    self._add_object_instance(new_object_instance)
                else:
                    object_instance = self._objects_map[object_hash]
                    coordinates = self.parent._get_coordinates(obj)
                    object_frame_instance_info = ObjectInstance.FrameInfo.from_dict(obj)

                    object_instance.set_for_frames(
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
                    new_classification_instance = self.parent._create_new_classification_instance(
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

    def _build_labels_dict(self) -> dict[str, LabelBlob]:
        """Build the labels dictionary for export."""
        labels: dict[str, LabelBlob] = {}

        for frame, label_hashes in self._get_tracked_frames_and_hashes():
            object_list = []
            classification_list = []

            for label_hash in label_hashes:
                frame_object_instance = self._objects_map.get(label_hash)
                frame_classification_instance = self._classifications_map.get(label_hash)

                if frame_object_instance is None and frame_classification_instance is None:
                    continue
                elif frame_object_instance is not None:
                    object_list.append(self.parent._to_encord_object(frame_object_instance, frame))
                else:
                    classification_list.append(
                        self.parent._to_encord_classification(frame_classification_instance, frame)
                    )

            labels[str(frame)] = LabelBlob(objects=object_list, classifications=classification_list)

        return labels

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


class VideoSpace(FrameBasedSpace):
    """Video space implementation for frame-based video annotations."""

    def __init__(self, space_id: str, title: str, parent: LabelRowV2, number_of_frames: int):
        super().__init__(space_id, title, SpaceType.VIDEO, parent)
        self._frames_to_hashes: defaultdict[int, Set[str]] = defaultdict(set)
        self._number_of_frames: int = number_of_frames

    def _track_hash_for_frames(self, item_hash: str, frames: Iterable[int]) -> None:
        for frame in frames:
            self._frames_to_hashes[frame].add(item_hash)

    def _untrack_hash_for_frames(self, item_hash: str, frames: Iterable[int]) -> None:
        for frame in frames:
            self._frames_to_hashes[frame].discard(item_hash)

    def _get_frames_to_process(self, space_info: BaseSpaceInfo) -> Iterable[tuple[int, LabelBlob]]:
        for frame_str, frame_label in space_info["labels"].items():
            yield (int(frame_str), frame_label)

    def _get_tracked_frames_and_hashes(self) -> Iterable[tuple[int, Set[str]]]:
        return self._frames_to_hashes.items()

    def add_object_instance(
        self, obj: Object, coordinates: TwoDimensionalCoordinates, frames: Frames = 0, **kwargs: Unpack[SetFramesKwargs]
    ) -> ObjectInstance:
        """Add an object instance to the video space."""
        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=coordinates, frames=frames, overwrite=False, **kwargs)
        return self._add_object_instance(object_instance)

    def add_classification_instance(
        self, classification: Classification, frames: Frames = 0, **kwargs: Unpack[SetFramesKwargs]
    ) -> ClassificationInstance:
        """Add a classification instance to the video space."""
        classification_instance = classification.create_instance()
        classification_instance.set_for_frames(frames=frames, overwrite=False, **kwargs)
        return self._add_classification_instance(classification_instance)

    def _to_space_dict(self) -> VideoSpaceInfo:
        """Export video space to dictionary format."""
        labels = self._build_labels_dict()
        return VideoSpaceInfo(
            space_type=self.space_type,
            labels=labels,
            number_of_frames=self._number_of_frames,
        )


class ImageSpace(FrameBasedSpace):
    """Image space implementation for single-frame image annotations."""

    def __init__(self, space_id: str, title: str, parent: LabelRowV2):
        super().__init__(space_id, title, SpaceType.IMAGE, parent)
        self._label_hashes: set[str] = set()

    def _track_hash_for_frames(self, item_hash: str, frames: Iterable[int]) -> None:
        """Track a hash (images only have frame 0, so just add to set)."""
        self._label_hashes.add(item_hash)

    def _untrack_hash_for_frames(self, item_hash: str, frames: Iterable[int]) -> None:
        """Untrack a hash (images only have frame 0, so just remove from set)."""
        self._label_hashes.discard(item_hash)

    def _get_frames_to_process(self, space_info: BaseSpaceInfo) -> Iterable[tuple[int, LabelBlob]]:
        """Get the single frame (frame 0) for image space."""
        frame_label = space_info["labels"].get("0")
        if frame_label is not None:
            yield 0, frame_label

    def _get_tracked_frames_and_hashes(self) -> Iterable[tuple[int, Set[str]]]:
        """Get frame 0 with all tracked hashes."""
        yield 0, self._label_hashes

    def add_object_instance(
        self, obj: Object, coordinates: TwoDimensionalCoordinates, **kwargs: Unpack[SetFramesKwargs]
    ) -> ObjectInstance:
        object_instance = obj.create_instance()
        object_instance.set_for_frames(coordinates=coordinates, frames=0, overwrite=False, **kwargs)
        return self._add_object_instance(object_instance)

    def add_classification_instance(
        self, classification: Classification, **kwargs: Unpack[SetFramesKwargs]
    ) -> ClassificationInstance:
        """Add a classification instance to the image space."""
        classification_instance = classification.create_instance()
        classification_instance.set_for_frames(frames=0, overwrite=False, **kwargs)
        return self._add_classification_instance(classification_instance)

    def _to_space_dict(self) -> ImageSpaceInfo:
        """Export image space to dictionary format."""
        labels = self._build_labels_dict()
        return ImageSpaceInfo(
            space_type=self.space_type,
            labels=labels,
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
