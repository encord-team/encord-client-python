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
    # is_deleted: Optional[bool] = None

    @staticmethod
    def from_dict(d: dict) -> "AnnotationInfo":
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

        return AnnotationInfo(
            created_at=parse_datetime(d["createdAt"]),
            created_by=d["createdBy"],
            last_edited_at=last_edited_at,
            last_edited_by=d.get("lastEditedBy"),
            confidence=d.get("confidence", DEFAULT_CONFIDENCE),
            manual_annotation=d.get("manualAnnotation", True),
            reviews=d.get("reviews"),
            # is_deleted=d.get("isDeleted"),
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
        if reviews is not None:
            self.reviews = reviews
        if is_deleted is not None:
            self.is_deleted = is_deleted


@dataclass
class AnnotationData:
    """Data class for storing annotation data.

    Attributes:
        annotation_info (AnnotationInfo): The annotation's metadata information.
    """

    annotation_info: AnnotationInfo


class Annotation:
    """Class providing common annotation metadata properties.

    Subclasses must implement:
        - _get_annotation_data() -> AnnotationData
        - _check_if_annotation_is_valid() -> None
    """

    @abstractmethod
    def _get_annotation_data(self) -> AnnotationData:
        """Get the underlying annotation data.

        Returns:
            AnnotationData: The annotation data containing metadata.
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
    def created_at(self) -> datetime:
        """Get the creation timestamp of the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.created_at

    @created_at.setter
    def created_at(self, created_at: datetime) -> None:
        """Set the creation timestamp of the annotation."""
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.created_at = created_at

    @property
    def created_by(self) -> Optional[str]:
        """Get the email of the user who created the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.created_by

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
        self._get_annotation_data().annotation_info.created_by = created_by

    @property
    def last_edited_at(self) -> datetime:
        """Get the last edited timestamp of the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.last_edited_at

    @last_edited_at.setter
    def last_edited_at(self, last_edited_at: datetime) -> None:
        """Set the last edited timestamp of the annotation."""
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.last_edited_at = last_edited_at

    @property
    def last_edited_by(self) -> Optional[str]:
        """Get the email of the user who last edited the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.last_edited_by

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
        self._get_annotation_data().annotation_info.last_edited_by = last_edited_by

    @property
    def confidence(self) -> float:
        """Get the confidence score of the annotation."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.confidence

    @confidence.setter
    def confidence(self, confidence: float) -> None:
        """Set the confidence score of the annotation."""
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.confidence = confidence

    @property
    def manual_annotation(self) -> bool:
        """Get whether this annotation was created manually."""
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.manual_annotation

    @manual_annotation.setter
    def manual_annotation(self, manual_annotation: bool) -> None:
        """Set whether this annotation was created manually."""
        self._check_if_annotation_is_valid()
        self._get_annotation_data().annotation_info.manual_annotation = manual_annotation

    @property
    def reviews(self) -> Optional[List[Dict[str, Any]]]:
        """Get the reviews for this annotation.

        Returns:
            Optional[List[Dict[str, Any]]]: A list of review dictionaries, if any.
        """
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.reviews

    # TODO: See if we can remove this
    @property
    def is_deleted(self) -> Optional[bool]:
        """Check if the annotation is marked as deleted.

        Returns:
            Optional[bool]: `True` if deleted, `False` otherwise, or `None` if not set.
        """
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().annotation_info.is_deleted


class ObjectAnnotation(Annotation):
    """Represents an object annotation on a Space.

    Provides access to annotation metadata for a SpaceObject.
    """

    def __init__(self, space: Space, object_instance: SpaceObject):
        self._space = space
        self._object_instance = object_instance

    @property
    def object_hash(self) -> str:
        """Get the hash of the object instance."""
        return self._object_instance.object_hash

    # Subclasses must implement these two methods
    @abstractmethod
    def _get_annotation_data(self) -> AnnotationData:
        pass

    @abstractmethod
    def _check_if_annotation_is_valid(self) -> None:
        pass


class ClassificationAnnotation(Annotation):
    """Represents a classification annotation on a Space.

    Allows setting or getting annotation data for the Classification.
    """

    def __init__(self, space: VideoSpace | ImageSpace | RangeBasedSpace, classification_instance: SpaceClassification):
        self._space = space
        self._classification_instance = classification_instance

    @property
    def classification_hash(self) -> str:
        """Get the hash of the object instance."""
        return self._classification_instance.classification_hash

    def _get_annotation_data(self) -> AnnotationData:
        return self._space._classification_hash_to_annotation_data[self._classification_instance.classification_hash]

    def _check_if_annotation_is_valid(self) -> None:
        if not self._classification_instance.classification_hash in self._space._classification_hash_to_annotation_data:
            raise LabelRowError("Annotation is invalid")
