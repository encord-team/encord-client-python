from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from encord.common.time_parser import parse_datetime
from encord.exceptions import LabelRowError
from encord.objects.constants import DEFAULT_CONFIDENCE, DEFAULT_MANUAL_ANNOTATION
from encord.objects.spaces.space_entity import SpaceClassification, SpaceObject
from encord.objects.utils import check_email

if TYPE_CHECKING:
    from encord.objects.spaces.base_space import Space
    from encord.objects.spaces.image_space import ImageSpace
    from encord.objects.spaces.range_space import RangeBasedSpace
    from encord.objects.spaces.video_space import VideoSpace


@dataclass
class AnnotationInfo:
    """Contains metadata information about a frame."""

    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    """None defaults to the user of the SDK once uploaded to the server."""
    last_edited_at: datetime = field(default_factory=datetime.now)
    last_edited_by: Optional[str] = None
    """None defaults to the user of the SDK once uploaded to the server."""
    confidence: float = DEFAULT_CONFIDENCE
    manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION
    reviews: Optional[List[dict]] = None
    # TODO: Classifications do not have this field
    is_deleted: Optional[bool] = None

    @staticmethod
    def from_dict(d: dict) -> "AnnotationInfo":
        """Create a FrameInfo instance from a dictionary.

        Args:
            d: A dictionary containing frame information.

        Returns:
            ObjectInstance.FrameInfo: An instance of FrameInfo.
        """
        if "lastEditedAt" in d and d["lastEditedAt"] is not None:
            last_edited_at = parse_datetime(d["lastEditedAt"])
        else:
            last_edited_at = datetime.now()

        return AnnotationInfo(
            created_at=parse_datetime(d["createdAt"]),
            created_by=d["createdBy"],
            last_edited_at=last_edited_at,
            last_edited_by=d.get("lastEditedBy"),
            confidence=d["confidence"],
            manual_annotation=d.get("manualAnnotation", True),
            reviews=d.get("reviews"),
            is_deleted=d.get("isDeleted"),
        )

    def update_from_optional_fields(
        self,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[Dict[str, Any]]] = None,
        is_deleted: Optional[bool] = None,
    ) -> None:
        """Update the FrameInfo fields with the specified values.

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
        if reviews is not None:
            self.reviews = reviews
        if is_deleted is not None:
            self.is_deleted = is_deleted


@dataclass
class AnnotationData:
    """Data class for storing frame-specific data.

    Attributes:
        annotation_info (ObjectInstance.FrameInfo): The frame's metadata information.
    """

    annotation_info: AnnotationInfo


class ObjectAnnotation:
    """Represents an annotation on a Space.

    Allows setting or getting annotation data for the ObjectInstance.
    """

    def __init__(self, space: Space, object_instance: SpaceObject):
        self._space = space
        self._object_instance = object_instance

    @property
    def created_at(self) -> datetime:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.created_at

    @created_at.setter
    def created_at(self, created_at: datetime) -> None:
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.created_at = created_at

    @property
    def created_by(self) -> Optional[str]:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.created_by

    @created_by.setter
    def created_by(self, created_by: Optional[str]) -> None:
        """Set the created_by field with a user email or None if it should default to the current user of the SDK."""
        self._check_if_annotation_is_valid()
        if created_by is not None:
            check_email(created_by)
        self._get_annotation_data().annotation_info.created_by = created_by

    @property
    def last_edited_at(self) -> datetime:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.last_edited_at

    @last_edited_at.setter
    def last_edited_at(self, last_edited_at: datetime) -> None:
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.last_edited_at = last_edited_at

    @property
    def last_edited_by(self) -> Optional[str]:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.last_edited_by

    @last_edited_by.setter
    def last_edited_by(self, last_edited_by: Optional[str]) -> None:
        """Set the last_edited_by field with a user email or None if it should default to the current user of the SDK."""
        self._check_if_annotation_is_valid()
        if last_edited_by is not None:
            check_email(last_edited_by)
        self._get_annotation_data().annotation_info.last_edited_by = last_edited_by

    @property
    def confidence(self) -> float:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.confidence

    @confidence.setter
    def confidence(self, confidence: float) -> None:
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.confidence = confidence

    @property
    def manual_annotation(self) -> bool:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.manual_annotation

    @manual_annotation.setter
    def manual_annotation(self, manual_annotation: bool) -> None:
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.manual_annotation = manual_annotation

    @property
    def reviews(self) -> Optional[List[Dict[str, Any]]]:
        """Get the reviews for this object on this frame.

        Returns:
            Optional[List[Dict[str, Any]]]: A list of review dictionaries, if any.
        """
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.reviews

    @property
    def is_deleted(self) -> Optional[bool]:
        """Check if the object instance is marked as deleted on this frame.

        Returns:
            Optional[bool]: `True` if deleted, `False` otherwise, or `None` if not set.
        """
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.is_deleted

    @abstractmethod
    def _get_annotation_data(self) -> AnnotationData:
        pass

    @abstractmethod
    def _check_if_annotation_is_valid(self) -> None:
        pass


class ClassificationAnnotation:
    """Represents an annotation on a Space.

    Allows setting or getting annotation data for the Classification.
    """

    def __init__(self, space: VideoSpace | ImageSpace | RangeBasedSpace, classification: SpaceClassification):
        self._space = space
        self._classification = classification

    @property
    def created_at(self) -> datetime:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.created_at

    @created_at.setter
    def created_at(self, created_at: datetime) -> None:
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.created_at = created_at

    @property
    def created_by(self) -> Optional[str]:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.created_by

    @created_by.setter
    def created_by(self, created_by: Optional[str]) -> None:
        """Set the created_by field with a user email or None if it should default to the current user of the SDK."""
        self._check_if_annotation_is_valid()
        if created_by is not None:
            check_email(created_by)
        self._get_annotation_data().annotation_info.created_by = created_by

    @property
    def last_edited_at(self) -> datetime:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.last_edited_at

    @last_edited_at.setter
    def last_edited_at(self, last_edited_at: datetime) -> None:
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.last_edited_at = last_edited_at

    @property
    def last_edited_by(self) -> Optional[str]:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.last_edited_by

    @last_edited_by.setter
    def last_edited_by(self, last_edited_by: Optional[str]) -> None:
        """Set the last_edited_by field with a user email or None if it should default to the current user of the SDK."""
        self._check_if_annotation_is_valid()
        if last_edited_by is not None:
            check_email(last_edited_by)
        self._get_annotation_data().annotation_info.last_edited_by = last_edited_by

    @property
    def confidence(self) -> float:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.confidence

    @confidence.setter
    def confidence(self, confidence: float) -> None:
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.confidence = confidence

    @property
    def manual_annotation(self) -> bool:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.manual_annotation

    @manual_annotation.setter
    def manual_annotation(self, manual_annotation: bool) -> None:
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.manual_annotation = manual_annotation

    @property
    def reviews(self) -> Optional[List[Dict[str, Any]]]:
        """Get the reviews for this object on this frame.

        Returns:
            Optional[List[Dict[str, Any]]]: A list of review dictionaries, if any.
        """
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.reviews

    @property
    def is_deleted(self) -> Optional[bool]:
        """Check if the object instance is marked as deleted on this frame.

        Returns:
            Optional[bool]: `True` if deleted, `False` otherwise, or `None` if not set.
        """
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.is_deleted

    def _get_annotation_data(self) -> AnnotationData:
        return self._space._classification_hash_to_annotation_data[self._classification.classification_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if not self._classification.classification_hash in self._space._classification_hash_to_annotation_data:
            raise LabelRowError("Annotation is invalid")
