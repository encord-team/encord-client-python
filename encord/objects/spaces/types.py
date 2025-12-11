from typing import Literal, Optional, TypedDict, Union

from encord.constants.enums import SpaceType
from encord.objects.types import LabelBlob


class BaseSpaceInfo(TypedDict):
    labels: dict[str, LabelBlob]


class ChildInfo(TypedDict):
    layout_key: str
    file_name: str


class VideoSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.VIDEO]
    child_info: ChildInfo
    number_of_frames: int
    width: int
    height: int


class ImageSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.IMAGE]
    child_info: ChildInfo
    width: int
    height: int


class TextSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.TEXT]
    child_info: ChildInfo


class AudioSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.AUDIO]
    child_info: ChildInfo
    duration_ms: int


SpaceInfo = Union[VideoSpaceInfo, ImageSpaceInfo, AudioSpaceInfo, TextSpaceInfo]
