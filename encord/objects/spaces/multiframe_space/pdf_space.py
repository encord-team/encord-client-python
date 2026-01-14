from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Sequence, Union

from encord.constants.enums import SpaceType
from encord.objects.answers import NumericAnswerValue
from encord.objects.attributes import Attribute
from encord.objects.coordinates import GeometricCoordinates
from encord.objects.frames import Frames
from encord.objects.ontology_object_instance import AnswersForFrames
from encord.objects.spaces.annotation.geometric_annotation import (
    _FrameClassificationAnnotation,
    _GeometricFrameObjectAnnotation,
)
from encord.objects.spaces.multiframe_space.multiframe_space import FrameOverlapStrategy, MultiFrameSpace
from encord.objects.spaces.types import PdfSpaceInfo, SpaceInfo

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance, Option
    from encord.objects.ontology_labels_impl import LabelRowV2


class PdfSpace(MultiFrameSpace):
    """PDF space implementation for page-based annotations.

    This class provides a page-centric API for PDF annotations, using 'pages' terminology
    instead of 'frames' for all public methods.
    """

    def __init__(
        self,
        space_id: str,
        label_row: LabelRowV2,
        space_info: SpaceInfo,
        number_of_pages: int,
    ):
        super().__init__(space_id, label_row, space_info, number_of_frames=number_of_pages)
        self._number_of_pages = number_of_pages

    def _get_frame_dimensions(self, frame: int) -> tuple[int, int]:
        # TODO: Currently we don't support adding bitmasks to PDF, we currently can't verify whether its a valid bitmasks
        # as we don't know the real width/height of the PDF
        return 0, 0

    def _to_space_dict(self) -> PdfSpaceInfo:
        """Export space to dictionary format."""
        frame_labels = self._build_frame_labels_dict()

        return PdfSpaceInfo(
            space_type=SpaceType.PDF,
            labels=frame_labels,
            number_of_pages=self._number_of_pages,
        )

    # ==================== Page-based API Methods ====================

    def put_object_instance(
        self,
        object_instance: ObjectInstance,
        pages: Frames,
        coordinates: GeometricCoordinates,
        *,
        on_overlap: FrameOverlapStrategy = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Add an object instance to specific pages in the PDF.

        Args:
            object_instance: The object instance to add to the PDF.
            pages: Page numbers or ranges where the object should appear. Can be:
                - A single page number (int)
                - A list of page numbers (List[int])
                - A Range object, specifying the start and end of the range (Range)
                - A list of Range objects for multiple ranges (List[Range])
            coordinates: Geometric coordinates for the object (e.g., bounding box, polygon, polyline).
            on_overlap: Strategy for handling existing annotations on the same pages.
                - "error" (default): Raises an error if annotation already exists.
                - "replace": Overwrites existing annotations on overlapping pages.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If pages are invalid or if annotation already exists when on_overlap="error".
        """
        super().put_object_instance(
            object_instance=object_instance,
            frames=pages,
            coordinates=coordinates,
            on_overlap=on_overlap,
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

    def put_classification_instance(
        self,
        classification_instance: ClassificationInstance,
        pages: Optional[Frames] = None,
        *,
        on_overlap: Optional[FrameOverlapStrategy] = "error",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Add a classification instance to specific pages in the PDF.

        Args:
            classification_instance: The classification instance to add to the PDF.
            pages: Page numbers or ranges where the classification should appear. Can be:
                - A single page number (int)
                - A list of page numbers (List[int])
                - A Range object, specifying the start and end of the range (Range)
                - A list of Range objects for multiple ranges (List[Range])
                For global classifications, set this to None.
            on_overlap: Strategy for handling existing classifications on the same pages.
                - "error" (default): Raises an error if classification already exists.
                - "replace": Overwrites existing classifications on overlapping pages.
            created_at: Optional timestamp when the annotation was created.
            created_by: Optional identifier of who created the annotation.
            last_edited_at: Optional timestamp when the annotation was last edited.
            last_edited_by: Optional identifier of who last edited the annotation.
            confidence: Optional confidence score for the annotation (0.0 to 1.0).
            manual_annotation: Optional flag indicating if this was manually annotated.

        Raises:
            LabelRowError: If pages are invalid or if classification already exists when on_overlap="error".
        """
        super().put_classification_instance(
            classification_instance=classification_instance,
            frames=pages,
            on_overlap=on_overlap,
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )

    def remove_object_instance(
        self,
        object_hash: str,
        pages: Optional[Frames] = None,
    ) -> Optional[ObjectInstance]:
        """Remove an object instance from pages on the pdf space. If no pages are provided, the object instance is removed
        from ALL pages in the pdf.

        Args:
            object_hash: The hash identifier of the object instance to remove.
            pages: The pages the object instance is to be removed from.

        Returns:
            Optional[ObjectInstance]: The removed object instance, or None if the object wasn't found.
        """
        return super().remove_object_instance(object_hash=object_hash, frames=pages)

    def remove_classification_instance(
        self, classification_hash: str, pages: Optional[Frames] = None
    ) -> Optional[ClassificationInstance]:
        return super().remove_classification_instance(classification_hash=classification_hash, frames=pages)
