from typing import Dict, List, Literal, Type, TypedDict, Union

from typing_extensions import NotRequired

from encord.constants.enums import SpaceType
from encord.exceptions import LabelRowError
from encord.objects.types import LabelBlob
from encord.utilities.type_utilities import exhaustive_guard


class BaseSpaceInfo(TypedDict):
    labels: Dict[str, LabelBlob]


class ChildInfo(TypedDict):
    layout_key: str
    file_name: str


class VideoSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.VIDEO]
    child_info: NotRequired[ChildInfo]
    number_of_frames: int
    width: int
    height: int


class ImageSequenceSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.IMAGE_SEQUENCE]
    child_info: NotRequired[ChildInfo]
    number_of_frames: int
    width: int
    height: int


class ImageSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.IMAGE]
    child_info: NotRequired[ChildInfo]
    width: int
    height: int


class TextSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.TEXT]
    child_info: NotRequired[ChildInfo]


class AudioSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.AUDIO]
    child_info: NotRequired[ChildInfo]
    duration_ms: int


class HtmlSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.HTML]
    child_info: NotRequired[ChildInfo]


class MedicalFileSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.MEDICAL_FILE]
    child_info: NotRequired[ChildInfo]
    number_of_frames: int
    width: int
    height: int


class DicomFrameInfo(TypedDict):
    width: int
    height: int
    instance_uid: str
    file_name: str


class MedicalStackSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.MEDICAL_STACK]
    child_info: NotRequired[ChildInfo]
    frames: List[DicomFrameInfo]


class FileInSceneInfo(TypedDict):
    stream_id: str
    event_index: int
    uri: str


class SceneImageSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.SCENE_IMAGE]
    scene_info: FileInSceneInfo


class PointCloudSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.POINT_CLOUD]


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
    PointCloudSpaceInfo,
]


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
    elif space_enum == SpaceType.POINT_CLOUD or space_enum == SpaceType.SCENE_IMAGE:
        raise LabelRowError(f"Space for {space_enum} not yet implemented.")
    else:
        exhaustive_guard(space_enum)
