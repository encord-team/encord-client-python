from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from encord.exceptions import LabelRowError
from encord.objects.classification_instance import BaseClassificationInstance
from encord.objects.coordinates import AudioCoordinates
from encord.objects.frames import Ranges
from encord.objects.ontology_object_instance import ObjectInstance
from encord.objects.spaces.annotation_instance.base_instance import BaseObjectInstance

if TYPE_CHECKING:
    from encord.objects.classification import Classification
    from encord.objects.ontology_object import Object
    from encord.objects.spaces.range_space import AudioSpace


class AudioObjectInstance(BaseObjectInstance):
    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None, space: AudioSpace):
        super().__init__(ontology_object, object_hash=object_hash)
        self._space = space
        self._annotation_data: Optional[AudioObjectInstance.AnnotationData] = None

    def get_annotation(self) -> Annotation:
        return AudioObjectInstance.Annotation(self)

    def add_annotation(
        self,
        ranges: Ranges,
        *,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        """Place the object onto the specified range.

        If the object already exists on the range and overwrite is set to `True`,
        the currently specified values will be overwritten.

        Args:
            ranges: The range to add the object instance to.
            created_at: Optionally specify the creation time of the object instance on this frame.
                Defaults to `datetime.now()`.
            created_by: Optionally specify the creator of the object instance on this frame.
                Defaults to the current SDK user.
            last_edited_at: Optionally specify the last edit time of the object instance on this frame.
                Defaults to `datetime.now()`.
            last_edited_by: Optionally specify the last editor of the object instance on this frame.
                Defaults to the current SDK user.
            confidence: Optionally specify the confidence of the object instance on this frame. Defaults to `1.0`.
            manual_annotation: Optionally specify whether the object instance on this frame was manually annotated. Defaults to `True`.
            reviews: Should only be set by internal functions.
            is_deleted: Should only be set by internal functions.
        """

        # audio_coordinates = AudioCoordinates(range=ranges)

        # No overwrite
        # No checking frame instance data, as its only on one frame

        if self._annotation_data is None:
            self._annotation_data = AudioObjectInstance.AnnotationData(
                ranges=ranges, object_frame_instance_info=BaseObjectInstance.AnnotationInfo()
            )

        self._annotation_data.object_frame_instance_info.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            reviews=reviews,
            is_deleted=is_deleted,
        )

    class Annotation(BaseObjectInstance.Annotation):
        def __init__(self, object_instance: AudioObjectInstance):
            super().__init__(object_instance)
            self._object_instance = object_instance

        @property
        def ranges(self) -> Ranges:
            self._check_if_annotation_is_valid()
            return self._get_annotation_data().ranges

        @ranges.setter
        def ranges(self, ranges: Ranges) -> None:
            self._check_if_annotation_is_valid()
            self._object_instance.add_annotation(ranges)

        def _get_annotation_data(self) -> AudioObjectInstance.AnnotationData:
            return self._object_instance._annotation_data

        def _check_if_annotation_is_valid(self) -> None:
            if self._object_instance._space is None:
                raise LabelRowError("Annotation does not exist on this audio")

    @dataclass
    class AnnotationData(BaseObjectInstance.AnnotationData):
        """Data class for storing annotation data on range objects.

        Attributes:
            object_frame_instance_info (ObjectInstance.FrameInfo): The frame's metadata information.
        """

        ranges: Ranges


class AudioClassificationInstance(BaseClassificationInstance):
    def __init__(
        self, ontology_classification: Classification, *, classification_hash: Optional[str] = None, space: AudioSpace
    ):
        super().__init__(ontology_classification, classification_hash=classification_hash)
        self._space = space
