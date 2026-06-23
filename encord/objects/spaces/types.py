from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Type, TypedDict, Union

from typing_extensions import NotRequired

from encord.constants.enums import SpaceType
from encord.objects.types import LabelBlob
from encord.utilities.type_utilities import exhaustive_guard


@dataclass(frozen=True)
class RootSpaceMetadata:
    """Metadata for root-level spaces."""

    file_name: str
    layout_key: None = None


@dataclass(frozen=True)
class DataGroupMetadata:
    """Metadata for spaces originating from a data group."""

    layout_key: Optional[str]
    file_name: str


@dataclass(frozen=True)
class SceneMetadata:
    """Metadata for spaces originating from a scene."""

    stream_id: str
    event_index: int
    start_frame: Optional[int]
    uri: str
    layout_key: None
    file_name: str
    """The name of the file, including extension, extracted from the URI."""


# Union of all metadata variants describing a space.
SpaceMetadata = Union[DataGroupMetadata, SceneMetadata, RootSpaceMetadata]


class BaseSpaceInfo(TypedDict):
    """Base information shared by all space info payloads."""

    labels: Dict[str, LabelBlob]


class ChildInfo(TypedDict):
    """Information about a child item within a layout-backed space."""

    layout_key: str
    file_name: str
    data_link: Optional[str]


class RootInfo(TypedDict):
    """Information about a root-level file associated with a space."""

    file_name: str


class VideoSpaceInfo(BaseSpaceInfo):
    """Information for a video space."""

    space_type: Literal[SpaceType.VIDEO]
    child_info: NotRequired[ChildInfo]
    number_of_frames: int
    width: int
    height: int
    data_duration: float
    data_fps: float


class ImageSequenceFrameInfo(TypedDict):
    """Information about a frame in an image sequence."""

    data_uuid: str
    data_type: str
    data_sequence: int
    data_link: str
    data_title: str


class ImageSequenceSpaceInfo(BaseSpaceInfo):
    """Information for an image sequence space."""

    space_type: Literal[SpaceType.IMAGE_SEQUENCE]
    child_info: NotRequired[ChildInfo]
    number_of_frames: int
    width: int
    height: int
    frames: List[ImageSequenceFrameInfo]


class ImageSpaceInfo(BaseSpaceInfo):
    """Information for an image space."""

    space_type: Literal[SpaceType.IMAGE]
    child_info: NotRequired[ChildInfo]
    root_info: NotRequired[RootInfo]
    width: int
    height: int


class TextSpaceInfo(BaseSpaceInfo):
    """Information for a text space."""

    space_type: Literal[SpaceType.TEXT]
    child_info: NotRequired[ChildInfo]


class AudioSpaceInfo(BaseSpaceInfo):
    """Information for an audio space."""

    space_type: Literal[SpaceType.AUDIO]
    child_info: NotRequired[ChildInfo]
    duration_ms: int


class HtmlSpaceInfo(BaseSpaceInfo):
    """Information for an HTML space."""

    space_type: Literal[SpaceType.HTML]
    child_info: NotRequired[ChildInfo]


class MedicalFileSpaceInfo(BaseSpaceInfo):
    """Information for a medical file space."""

    space_type: Literal[SpaceType.MEDICAL_FILE]
    child_info: NotRequired[ChildInfo]
    number_of_frames: int
    width: int
    height: int


class DicomFrameInfo(TypedDict):
    """Information about a frame in a DICOM stack."""

    width: int
    height: int
    instance_uid: str
    file_name: str


class MedicalStackSpaceInfo(BaseSpaceInfo):
    """Information for a medical stack space."""

    space_type: Literal[SpaceType.MEDICAL_STACK]
    child_info: NotRequired[ChildInfo]
    frames: List[DicomFrameInfo]


class FileInSceneInfo(TypedDict):
    """Information identifying a file within a scene."""

    stream_id: str
    event_index: int
    start_frame: NotRequired[int]
    uri: str


class PointCloudFileSpaceInfo(TypedDict):
    """Information for a point cloud file that is part of a scene."""

    space_type: Literal[SpaceType.POINT_CLOUD]
    scene_info: FileInSceneInfo
    labels: LabelBlob


class SceneImageSpaceInfo(TypedDict):
    """Information for an image file that is part of a scene."""

    space_type: Literal[SpaceType.SCENE_IMAGE]
    scene_info: FileInSceneInfo
    labels: LabelBlob
    width: NotRequired[int]
    height: NotRequired[int]


class PdfSpaceInfo(BaseSpaceInfo):
    """Information for a PDF space."""

    space_type: Literal[SpaceType.PDF]
    child_info: NotRequired[ChildInfo]
    number_of_pages: int


# Union of all possible space info payloads returned by the SDK.
SpaceInfo = Union[
    VideoSpaceInfo,
    ImageSpaceInfo,
    ImageSequenceSpaceInfo,
    AudioSpaceInfo,
    TextSpaceInfo,
    HtmlSpaceInfo,
    MedicalFileSpaceInfo,
    MedicalStackSpaceInfo,
    SceneImageSpaceInfo,
    PointCloudFileSpaceInfo,
    PdfSpaceInfo,
]


# type checking only; ensure we create a SpaceInfo for every SpaceType enum
def _get_space_info_from_space_enum(space_enum: SpaceType) -> Type[SpaceInfo]:
    if space_enum == SpaceType.VIDEO:
        return VideoSpaceInfo
    elif space_enum == SpaceType.IMAGE:
        return ImageSpaceInfo
    elif space_enum == SpaceType.IMAGE_SEQUENCE:
        return ImageSequenceSpaceInfo
    elif space_enum == SpaceType.AUDIO:
        return AudioSpaceInfo
    elif space_enum == SpaceType.TEXT:
        return TextSpaceInfo
    elif space_enum == SpaceType.HTML:
        return HtmlSpaceInfo
    elif space_enum == SpaceType.MEDICAL_FILE:
        return MedicalFileSpaceInfo
    elif space_enum == SpaceType.MEDICAL_STACK:
        return MedicalStackSpaceInfo
    elif space_enum == SpaceType.PDF:
        return PdfSpaceInfo
    elif space_enum == SpaceType.POINT_CLOUD:
        return PointCloudFileSpaceInfo
    elif space_enum == SpaceType.SCENE_IMAGE:
        return SceneImageSpaceInfo
    else:
        exhaustive_guard(space_enum)
