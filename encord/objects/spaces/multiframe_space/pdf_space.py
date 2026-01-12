from __future__ import annotations

from typing import TYPE_CHECKING

from encord.constants.enums import SpaceType
from encord.objects.spaces.multiframe_space.multiframe_space import MultiFrameSpace
from encord.objects.spaces.types import PdfSpaceInfo

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2


class PdfSpace(MultiFrameSpace):
    """PDF space implementation for page-based annotations."""

    def __init__(
        self,
        space_id: str,
        label_row: LabelRowV2,
        number_of_pages: int,
    ):
        super().__init__(space_id, label_row, number_of_frames=number_of_pages)
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
