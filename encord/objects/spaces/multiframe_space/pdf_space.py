from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Sequence, Union

from encord.constants.enums import SpaceType
from encord.objects.answers import NumericAnswerValue
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
    from encord.objects import Attribute, ClassificationInstance, ObjectInstance, Option
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

    def remove_object_instance_from_pages(
        self,
        object_instance: ObjectInstance,
        pages: Frames,
    ) -> List[int]:
        """Remove an object instance from specific pages in the PDF.

        If the object is removed from all pages, it will be completely removed from the space.
        All dynamic answers associated with the object on these pages will also be removed.

        Args:
            object_instance: The object instance to remove from pages.
            pages: Page numbers or ranges to remove the object from. Can be:
                - A single page number (int)
                - A list of page numbers (List[int])
                - A Range object, specifying the start and end of the range (Range)
                - A list of Range objects for multiple ranges (List[Range])

        Returns:
            List[int]: List of page numbers where the object was actually removed.
                Empty if the object didn't exist on any of the specified pages.
        """
        return super().remove_object_instance_from_frames(
            object_instance=object_instance,
            frames=pages,
        )

    def set_answer_on_pages(
        self,
        object_instance: ObjectInstance,
        pages: Frames,
        answer: Union[str, NumericAnswerValue, Option, Sequence[Option]],
        attribute: Optional[Attribute] = None,
    ) -> None:
        """Set dynamic attribute answers for an object instance on specific pages.

        This method is only for dynamic attributes. For static attributes, use `ObjectInstance.set_answer`.

        Args:
            object_instance: The object instance to set answers for.
            pages: Page numbers or ranges where the answer should be applied.
            answer: The answer value. Can be:
                - str: For text attributes
                - float/int: For numeric attributes
                - Option: For radio attributes
                - Sequence[Option]: For checklist attributes
            attribute: The attribute to set the answer for. If None, will be inferred from the answer type.

        Raises:
            LabelRowError: If the attribute is not dynamic, not a valid child of the object,
                or if the object doesn't exist on the space yet.
        """
        super().set_answer_on_frames(
            object_instance=object_instance,
            frames=pages,
            answer=answer,
            attribute=attribute,
        )

    def remove_answer_from_page(
        self,
        object_instance: ObjectInstance,
        attribute: Attribute,
        page: int,
        filter_answer: Optional[Union[str, Option, Sequence[Option]]] = None,
    ) -> None:
        """Remove a dynamic attribute answer from an object instance on a specific page.

        Args:
            object_instance: The object instance to remove the answer from.
            attribute: The dynamic attribute whose answer should be removed.
            page: The page number to remove the answer from.
            filter_answer: Optional filter to remove only specific answer values.
                For checklist attributes, can specify which options to remove.

        Raises:
            LabelRowError: If the attribute is not dynamic or if the object doesn't exist on the space.
        """
        super().remove_answer_from_frame(
            object_instance=object_instance,
            attribute=attribute,
            frame=page,
            filter_answer=filter_answer,
        )

    def get_answer_on_pages(
        self,
        object_instance: ObjectInstance,
        pages: Frames,
        attribute: Attribute,
        filter_answer: Union[str, NumericAnswerValue, Option, Sequence[Option], None] = None,
    ) -> AnswersForFrames:
        """Get dynamic attribute answers for an object instance on specific pages.

        This method is only for dynamic attributes. For static attributes, use `ObjectInstance.get_answer`.

        Args:
            object_instance: The object instance to get answers from.
            pages: Page numbers or ranges to retrieve answers for.
            attribute: The dynamic attribute to get answers for.
            filter_answer: Optional filter to retrieve only specific answer values.

        Returns:
            AnswersForFrames: Dictionary mapping pages to their corresponding answers.

        Raises:
            LabelRowError: If the attribute is not dynamic or if the object doesn't exist on the space.
        """
        return super().get_answer_on_frames(
            object_instance=object_instance,
            frames=pages,
            attribute=attribute,
            filter_answer=filter_answer,
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

    def remove_classification_instance_from_pages(
        self,
        classification_instance: ClassificationInstance,
        pages: Frames,
    ) -> List[int]:
        """Remove a classification instance from specific pages in the PDF.

        If the classification is removed from all pages, it will be completely removed from the space.

        Args:
            classification_instance: The classification instance to remove from pages.
            pages: Page numbers or ranges to remove the classification from. Can be:
                - A single page number (int)
                - A list of page numbers (List[int])
                - A Range object, specifying the start and end of the range (Range)
                - A list of Range objects for multiple ranges (List[Range])

        Returns:
            List[int]: List of page numbers where the classification was actually removed.
                Empty if the classification didn't exist on any of the specified pages.
        """
        return super().remove_classification_instance_from_frames(
            classification_instance=classification_instance,
            frames=pages,
        )

    def get_annotations_by_page(
        self,
        type_: Literal["object", "classification"],
    ) -> Union[Dict[int, List[_GeometricFrameObjectAnnotation]], Dict[int, List[_FrameClassificationAnnotation]]]:
        """Get all annotations organized by page number.

        Args:
            type_: Type of annotations to retrieve:
                - "object": Get object instance annotations
                - "classification": Get classification instance annotations

        Returns:
            Dictionary mapping page numbers to lists of annotations on that page.
            The annotation type depends on the type_ parameter:
            - When type_="object": Dict[int, List[_GeometricFrameObjectAnnotation]]
            - When type_="classification": Dict[int, List[_FrameClassificationAnnotation]]
        """
        return super().get_annotations_by_frame(type_=type_)

    # ==================== Disabled Frame-based Methods ====================
    # These raise helpful errors if someone tries to use frame terminology

    def remove_object_instance_from_frames(self, *args, **kwargs):
        raise AttributeError(
            "PdfSpace uses 'remove_object_instance_from_pages' instead of 'remove_object_instance_from_frames'. "
            "Use page numbers instead of frame numbers."
        )

    def set_answer_on_frames(self, *args, **kwargs):
        raise AttributeError(
            "PdfSpace uses 'set_answer_on_pages' instead of 'set_answer_on_frames'. "
            "Use page numbers instead of frame numbers."
        )

    def remove_answer_from_frame(self, *args, **kwargs):
        raise AttributeError(
            "PdfSpace uses 'remove_answer_from_page' instead of 'remove_answer_from_frame'. "
            "Use page numbers instead of frame numbers."
        )

    def get_answer_on_frames(self, *args, **kwargs):
        raise AttributeError(
            "PdfSpace uses 'get_answer_on_pages' instead of 'get_answer_on_frames'. "
            "Use page numbers instead of frame numbers."
        )

    def remove_classification_instance_from_frames(self, *args, **kwargs):
        raise AttributeError(
            "PdfSpace uses 'remove_classification_instance_from_pages' instead of 'remove_classification_instance_from_frames'. "
            "Use page numbers instead of frame numbers."
        )

    def get_annotations_by_frame(self, *args, **kwargs):
        raise AttributeError(
            "PdfSpace uses 'get_annotations_by_page' instead of 'get_annotations_by_frame'. "
            "Use page numbers instead of frame numbers."
        )
