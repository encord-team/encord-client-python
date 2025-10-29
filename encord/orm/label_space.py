from typing import Literal, TypedDict, Union

from encord.constants.enums import SpaceType


class LabelBlob(TypedDict):
    objects: list[dict]
    classifications: list[dict]


class BaseSpaceInfo(TypedDict):
    labels: dict[str, LabelBlob]


class VideoSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.VIDEO]
    number_of_frames: int
    width: int
    height: int


class ImageSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.IMAGE]
    width: int
    height: int


class TextSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.TEXT]
    number_of_characters: int


class AudioSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.AUDIO]
    duration_ms: int


class PointCloudSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.POINT_CLOUD]


SpaceInfo = Union[VideoSpaceInfo, AudioSpaceInfo, ImageSpaceInfo, TextSpaceInfo]
