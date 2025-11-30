from typing import Literal, TypedDict, Union

from encord.constants.enums import SpaceType
from encord.objects.types import LabelBlob


class BaseSpaceInfo(TypedDict):
    labels: dict[str, LabelBlob]


class ChildInfo(TypedDict):
    """Information for child of a data group"""

    is_readonly: bool
    layout_key: str
    file_name: str


class VideoSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.VIDEO]
    info: ChildInfo
    number_of_frames: int
    width: int
    height: int


class ImageSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.IMAGE]
    info: ChildInfo

    width: int
    height: int


#
# class TextSpaceInfo(BaseSpaceInfo):
#     space_type: Literal[SpaceType.TEXT]
#     number_of_characters: int
#
#
class AudioSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.AUDIO]
    info: ChildInfo
    duration_ms: int


SpaceInfo = Union[VideoSpaceInfo, ImageSpaceInfo, AudioSpaceInfo]

