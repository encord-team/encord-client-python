from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from encord.exceptions import LabelRowError
from encord.objects.classification_instance import BaseClassificationInstance
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import Coordinates, TwoDimensionalCoordinates
from encord.objects.frames import Frames, frames_class_to_frames_list
from encord.objects.ontology_object_instance import BaseObjectInstance, ObjectInstance, check_coordinate_type

if TYPE_CHECKING:
    from encord.objects.classification import Classification
    from encord.objects.ontology_object import Object
    from encord.objects.spaces.frame_space import ImageSpace


class ImageObjectInstance(BaseObjectInstance):
    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None, space: ImageSpace):
        super().__init__(ontology_object, object_hash=object_hash)
        self._space = space

    def set_annotation(
        self,
        coordinates: TwoDimensionalCoordinates,
        *,
        overwrite: bool = False, #TODO: remove this
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        """Place the object onto the image.

        If the object already exists and overwrite is set to `True`,
        the currently specified values will be overwritten.

        Args:
            coordinates: The coordinates of the object.
                This will throw an error if the type of the coordinates does not match the type of the attribute in the object instance.
            overwrite: If `True`, overwrite existing data.
                This will not reset all the non-specified values.
                If `False` and data already exists, raises an error.
            created_at: Optionally specify the creation time of the object instance.
                Defaults to `datetime.now()`.
            created_by: Optionally specify the creator of the object instance.
                Defaults to the current SDK user.
            last_edited_at: Optionally specify the last edit time of the object instance.
                Defaults to `datetime.now()`.
            last_edited_by: Optionally specify the last editor of the object instance.
                Defaults to the current SDK user.
            confidence: Optionally specify the confidence of the object instance. Defaults to `1.0`.
            manual_annotation: Optionally specify whether the object instance was manually annotated. Defaults to `True`.
            reviews: Should only be set by internal functions.
            is_deleted: Should only be set by internal functions.
        """

        # For image, there is only one frame, i.e. frame=0
        frame = 0
        existing_frame_data = self._frames_to_instance_data.get(frame)

        if overwrite is False and existing_frame_data is not None:
            raise LabelRowError(
                "Cannot overwrite existing data. Set `overwrite` to `True` to overwrite."
            )

        # TODO: Remove this self._parent requirement
        check_coordinate_type(coordinates, self._ontology_object, self._parent)

        if existing_frame_data is None:
            existing_frame_data = ObjectInstance.FrameData(
                coordinates=coordinates, object_frame_instance_info=ObjectInstance.FrameInfo()
            )
            self._frames_to_instance_data[frame] = existing_frame_data

        existing_frame_data.object_frame_instance_info.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            reviews=reviews,
            is_deleted=is_deleted,
        )
        existing_frame_data.coordinates = coordinates

    def remove_annotation(self) -> None:
        """Remove the object instance from the specified frames.
        """
        self._frames_to_instance_data.pop(0)





class ImageClassificationInstance(BaseClassificationInstance):
    def __init__(self, ontology_classification: Classification, *, classification_hash: Optional[str] = None, space: ImageSpace):
        super().__init__(ontology_classification, classification_hash=classification_hash)
        self._space = space

    def set_annotation(
        self,
        *,
        created_at: Optional[datetime] = datetime.now(),
        created_by: Optional[str] = None,
        confidence: float = DEFAULT_CONFIDENCE,
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
        last_edited_at: Optional[datetime] = datetime.now(),
        last_edited_by: Optional[str] = None,
        reviews: Optional[List[dict]] = None,
    ) -> None:
        """Places the classification onto the image. If the classification already exists and
        overwrite is set to `True`, the currently specified values will be overwritten.

        Args:
            created_at: Optionally specify the creation time of the classification instance. Defaults to `datetime.now()`.
            created_by: Optionally specify the creator of the classification instance. Defaults to the current SDK user.
            last_edited_at: Optionally specify the last edit time of the classification instance. Defaults to `datetime.now()`.
            last_edited_by: Optionally specify the last editor of the classification instance. Defaults to the current SDK
                user.
            confidence: Optionally specify the confidence of the classification instance. Defaults to `1.0`.
            manual_annotation: Optionally specify whether the classification instance was manually annotated. Defaults to `True`.
            reviews: Should only be set by internal functions.
        """

        self._set_frame_and_frame_data(
            frame=0,
            # TODO: Ask someone if this is fine
            overwrite=True,
            created_at=created_at,
            created_by=created_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            reviews=reviews,
        )
