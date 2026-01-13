from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Literal, Optional, TypedDict, TypeGuard

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.spaces.multiframe_space.multiframe_space import MultiFrameSpace
from encord.objects.spaces.types import DicomFrameInfo, MedicalFileSpaceInfo, MedicalStackSpaceInfo, SpaceInfo
from encord.objects.types import LabelBlob

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2

logger = logging.getLogger(__name__)


class MedicalStackInfo(TypedDict):
    frames: List[DicomFrameInfo]


class MedicalFileInfo(TypedDict):
    width: int
    height: int
    number_of_frames: int


def _is_medical_file(space_info: SpaceInfo) -> TypeGuard[MedicalFileSpaceInfo]:
    return space_info["space_type"] == SpaceType.MEDICAL_FILE


def _is_medical_stack(space_info: SpaceInfo) -> TypeGuard[MedicalStackSpaceInfo]:
    return space_info["space_type"] == SpaceType.MEDICAL_STACK


class MedicalSpace(MultiFrameSpace):
    """
    Space for medical files (e.g. DICOM, NIfTI). It handles both medical-file and medical-stack.
        Medical-file: Single files with multiple frames.
        Medical-stack: Multiple files where frames on each file may have different dimensions.
    """

    def __init__(
        self,
        space_id: str,
        label_row: LabelRowV2,
        space_info: SpaceInfo,
    ):
        self._width: int | None = None
        self._height: int | None = None
        self._number_of_frames: int
        self._frames: List[DicomFrameInfo] | None = None
        self._space_info = space_info

        if _is_medical_file(space_info):
            self._width = space_info["width"]
            self._height = space_info["height"]
            self._number_of_frames = space_info["number_of_frames"]

        elif _is_medical_stack(space_info):
            self._number_of_frames = len(space_info["frames"])
            self._frames = space_info["frames"]

        else:
            raise LabelRowError("This medical space has invalid space information.")

        super().__init__(space_id, label_row, space_info, number_of_frames=self._number_of_frames)

    def _get_frame_dimensions(self, frame: int) -> tuple[int, int]:
        if _is_medical_stack(self._space_info):
            frame_info = self._space_info["frames"][frame]
            return frame_info["width"], frame_info["height"]
        elif _is_medical_file(self._space_info):
            return self._space_info["width"], self._space_info["height"]
        else:
            raise LabelRowError("This medical space is invalid. It does not contain frame dimensions.")

    def _to_space_dict(self) -> MedicalFileSpaceInfo | MedicalStackSpaceInfo:
        """Export space to dictionary format."""
        frame_labels = self._build_frame_labels_dict()

        if _is_medical_file(self._space_info):
            return MedicalFileSpaceInfo(
                space_type=SpaceType.MEDICAL_FILE,
                labels=frame_labels,
                number_of_frames=self._number_of_frames,
                width=self._space_info["width"],
                height=self._space_info["height"],
            )
        elif _is_medical_stack(self._space_info):
            return MedicalStackSpaceInfo(
                space_type=SpaceType.MEDICAL_STACK, labels=frame_labels, frames=self._space_info["frames"]
            )
        else:
            raise LabelRowError("This medical space is invalid. It contains incorrect space information")
