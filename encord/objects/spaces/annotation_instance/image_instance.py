from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from encord.exceptions import LabelRowError
from encord.objects.classification_instance import BaseClassificationInstance
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import Coordinates, TwoDimensionalCoordinates
from encord.objects.ontology_object_instance import check_coordinate_type
from encord.objects.spaces.annotation_instance.base_instance import BaseObjectInstance

if TYPE_CHECKING:
    from encord.objects.classification import Classification
    from encord.objects.ontology_object import Object
    from encord.objects.spaces.video_space import ImageSpace


class ImageObjectInstance(BaseObjectInstance):
    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None, space: ImageSpace):
        super().__init__(ontology_object, object_hash=object_hash)
        self._space = space
        self._annotation: Optional[ImageObjectInstance.AnnotationData] = None

    def get_annotation(self) -> Annotation:
        return ImageObjectInstance.Annotation(self)

    def add_annotation(
        self,
        coordinates: TwoDimensionalCoordinates,
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
        """Place the object onto the image.

        If the object already exists and overwrite is set to `True`,
        the currently specified values will be overwritten.

        Args:
            coordinates: The coordinates of the object.
                This will throw an error if the type of the coordinates does not match the type of the attribute in the object instance.
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

        # TODO: Remove this self._parent requirement
        check_coordinate_type(coordinates, self._ontology_object, self._parent)

        if self._annotation is None:
            existing_frame_data = BaseObjectInstance.AnnotationData(
                coordinates=coordinates, object_frame_instance_info=BaseObjectInstance.AnnotationInfo()
            )
            self._annotation = existing_frame_data

        self._annotation.object_frame_instance_info.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            reviews=reviews,
            is_deleted=is_deleted,
        )
        self._annotation.coordinates = coordinates

    def remove_annotation(self) -> None:
        """Remove the object instance from the specified frames."""
        self._annotation = None

    class Annotation(BaseObjectInstance.Annotation):
        def __init__(self, object_instance: ImageObjectInstance):
            super().__init__(object_instance)
            self._object_instance = object_instance

        @property
        def coordinates(self) -> Coordinates:
            self._check_if_annotation_is_valid()
            return self._get_annotation_data().coordinates

        @coordinates.setter
        def coordinates(self, coordinates: Coordinates) -> None:
            self._check_if_annotation_is_valid()
            self._object_instance.add_annotation(coordinates)

        def _get_annotation_data(self) -> BaseObjectInstance.AnnotationData:
            return self._object_instance._annotation

        def _check_if_annotation_is_valid(self) -> None:
            if self._object_instance._space is None:
                raise LabelRowError("Annotation does not exist on this image")


class ImageClassificationInstance(BaseClassificationInstance):
    def __init__(
        self, ontology_classification: Classification, *, classification_hash: Optional[str] = None, space: ImageSpace
    ):
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
