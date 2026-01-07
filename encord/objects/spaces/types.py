from typing import Literal, TypedDict, Union

from typing_extensions import NotRequired

from encord.constants.enums import SpaceType
from encord.objects.types import LabelBlob


class BaseSpaceInfo(TypedDict):
    labels: dict[str, LabelBlob]


class ChildInfo(TypedDict):
    layout_key: str
    file_name: str


class MedicalFileSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.MEDICAL_FILE]
    child_info: NotRequired[ChildInfo]
    number_of_frames: int
    width: int
    height: int


class VideoSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.VIDEO]
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


SpaceInfo = Union[VideoSpaceInfo, ImageSpaceInfo, AudioSpaceInfo, TextSpaceInfo, HtmlSpaceInfo]
