from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from encord.common.time_parser import parse_datetime
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import Coordinates
from encord.objects.types import BaseFrameObject, ClassificationAnswer, FrameClassification
from encord.objects.utils import check_email

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance
    from encord.objects.spaces.base_space import Space
    from encord.objects.spaces.image_space import ImageSpace
    from encord.objects.spaces.range_space.range_space import RangeSpace
    from encord.objects.spaces.video_space import VideoSpace

logger = logging.getLogger(__name__)


@dataclass
class _AnnotationMetadata:
    """Contains metadata information about an annotation (on a frame or a range)"""

    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    """None defaults to the user of the SDK once uploaded to the server."""
    last_edited_at: datetime = field(default_factory=datetime.now)
    last_edited_by: Optional[str] = None
    """None defaults to the user of the SDK once uploaded to the server."""
    confidence: float = DEFAULT_CONFIDENCE
    manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION
    # TODO: Classifications do not have this field. We also want to deprecate this field.
    is_deleted: Optional[bool] = None
    # TODO: We want tod deprecate this field.
    reviews: Optional[List[dict[Any, Any]]] = None

    @staticmethod
    def from_dict(d: BaseFrameObject | FrameClassification | ClassificationAnswer) -> "_AnnotationMetadata":
        """Create a AnnotationInfo instance from a dictionary.
        Args:
            d: A dictionary containing information about the annotation.
        Returns:
            AnnotationInfo: An instance of AnnotationInfo.
        """
        if "lastEditedAt" in d and d["lastEditedAt"] is not None:
            last_edited_at = parse_datetime(d["lastEditedAt"])
        else:
            last_edited_at = datetime.now()

        confidence = d.get("confidence", None)
        manual_annotation = d.get("manualAnnotation", None)
        created_at = d["createdAt"]
        return _AnnotationMetadata(
            created_at=parse_datetime(created_at) if created_at is not None else datetime.now(),
            created_by=d.get("createdBy", None),
            last_edited_at=last_edited_at,
            last_edited_by=d.get("lastEditedBy", None),
            confidence=confidence if confidence is not None else DEFAULT_CONFIDENCE,
            manual_annotation=manual_annotation if manual_annotation is not None else DEFAULT_MANUAL_ANNOTATION,
            reviews=d.get("reviews", None),  # Only here for backwards compatibility, do not use this
            is_deleted=cast(
                Optional[bool], d.get("isDeleted", None)
            ),  # Only here for backwards compatibility, do not use this
        )

    def update_from_optional_fields(
        self,
        *,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        is_deleted: Optional[bool] = None,  # This field is deprecated. Please do not use this field.
        reviews: Optional[List[Dict[Any, Any]]] = None,  # This field is deprecated. Please do not use this field.
    ) -> None:
        """Update the AnnotationInfo fields with the specified values.
        Args:
            created_at: Optional creation time.
            created_by: Optional creator identifier.
            last_edited_at: Optional last edited time.
            last_edited_by: Optional last editor identifier.
            confidence: Optional confidence value.
            manual_annotation: Optional manual annotation flag.
            reviews: Optional list of reviews.
            is_deleted: Optional deleted flag.
        """
        self.created_at = created_at or self.created_at
        if created_by is not None:
            self.created_by = created_by
        self.last_edited_at = last_edited_at or self.last_edited_at
        if last_edited_by is not None:
            self.last_edited_by = last_edited_by
        if confidence is not None:
            self.confidence = confidence
        if manual_annotation is not None:
            self.manual_annotation = manual_annotation
        if is_deleted is not None:
            self.is_deleted = is_deleted
        if reviews is not None:
            self.reviews = reviews


@dataclass
class _AnnotationData:
    """
    Data class for storing annotation data (e.g. coordinates, range) and metadata.
    Only metadata in the base class, but subclasses will have more. E.g. GeometricAnnotationData has coordinates.
    Attributes:
        annotation_metadata (_AnnotationMetadata): The annotation's metadata information.
    """

    annotation_metadata: _AnnotationMetadata


class _Annotation(ABC):
    """
    Class providing common annotation properties.
    """

    def __init__(self, space: Space):
        self._space = space

    @abstractmethod
    def _get_annotation_data(self) -> _AnnotationData:
        """Get the underlying annotation data.
        Returns:
            _AnnotationData: The annotation data, which contains information about the annotation (including metadata).
        """
        pass

    @abstractmethod
    def _check_if_annotation_is_valid(self) -> None:
        """Validate that the annotation still exists and is accessible.
        Raises:
            LabelRowError: If the annotation is no longer valid.
        """
        pass

    @property
    @abstractmethod
    def frame(self) -> int:
        """int: Gets the frame number.

        Note:
            This is a legacy attribute. For new subclasses where frame
            is not applicable (e.g. audio and text), this returns 0.
        """
        pass

    @property
    @abstractmethod
    def space(self) -> Space:
        """Get the space that this annotation is on."""
        pass

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp of the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_metadata.created_at

    @created_at.setter
    def created_at(self, created_at: datetime) -> None:
        """Set the creation timestamp of the annotation."""
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_metadata.created_at = created_at

    @property
    def created_by(self) -> Optional[str]:
        """Get the email of the user who created the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_metadata.created_by

    @created_by.setter
    def created_by(self, created_by: Optional[str]) -> None:
        """Set the creator email. None defaults to the current SDK user.
        Args:
            created_by: User email or None to default to SDK user.
        Raises:
            ValueError: If the email format is invalid.
        """
        self._check_if_annotation_is_valid()
        if created_by is not None:
            check_email(created_by)
        self._get_annotation_data().annotation_metadata.created_by = created_by

    @property
    def last_edited_at(self) -> datetime:
        """Get the last edited timestamp of the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_metadata.last_edited_at

    @last_edited_at.setter
    def last_edited_at(self, last_edited_at: datetime) -> None:
        """Set the last edited timestamp of the annotation."""
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_metadata.last_edited_at = last_edited_at

    @property
    def last_edited_by(self) -> Optional[str]:
        """Get the email of the user who last edited the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_metadata.last_edited_by

    @last_edited_by.setter
    def last_edited_by(self, last_edited_by: Optional[str]) -> None:
        """Set the last editor email. None defaults to the current SDK user.
        Args:
            last_edited_by: User email or None to default to SDK user.
        Raises:
            ValueError: If the email format is invalid.
        """
        self._check_if_annotation_is_valid()
        if last_edited_by is not None:
            check_email(last_edited_by)
        self._get_annotation_data().annotation_metadata.last_edited_by = last_edited_by

    @property
    def confidence(self) -> float:
        """Get the confidence score of the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_metadata.confidence

    @confidence.setter
    def confidence(self, confidence: float) -> None:
        """Set the confidence score of the annotation."""
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_metadata.confidence = confidence

    @property
    def manual_annotation(self) -> bool:
        """Get whether this annotation was created manually."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_metadata.manual_annotation

    @manual_annotation.setter
    def manual_annotation(self, manual_annotation: bool) -> None:
        """Set whether this annotation was created manually."""
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_metadata.manual_annotation = manual_annotation


class _ObjectAnnotation(_Annotation):
    """Represents an object annotation on a Space.
    Provides access to annotation metadata for a SpaceObject.
    """

    def __init__(self, space: Space, object_instance: ObjectInstance):
        super().__init__(space)
        self._object_instance = object_instance

    @property
    def object_instance(self) -> ObjectInstance:
        return self._object_instance

    @property
    def object_hash(self) -> str:
        """Get the hash of the object instance."""
        return self._object_instance.object_hash

    @property
    @abstractmethod
    def coordinates(self) -> Coordinates:
        """coordinates: Gets the frame number.

        Note:
            This is a legacy attribute. For new subclasses where coordinates
            are not applicable, do not use this attribute. Instead, use `.ranges` instead (e.g. for audio or text spaces)
        """
        pass


class _ClassificationAnnotation(_Annotation):
    """Represents a classification annotation on a Space.
    Allows setting or getting annotation data for the Classification.
    """

    def __init__(self, space: Space, classification_instance: ClassificationInstance):
        super().__init__(space)
        self._classification_instance = classification_instance

    @property
    def classification_instance(self) -> ClassificationInstance:
        return self._classification_instance

    @property
    def classification_hash(self) -> str:
        """Get the hash of the object instance."""
        return self._classification_instance.classification_hash
