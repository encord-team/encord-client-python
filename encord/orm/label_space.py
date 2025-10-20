from typing import Literal, TypedDict, Union

from encord.constants.enums import SpaceType


class LabelBlob(TypedDict):
    objects: list[dict]
    classifications: list[dict]


class BaseSpaceInfo(TypedDict):
    space_type: SpaceType
    labels: dict[str, LabelBlob]


class VideoSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.VIDEO]
    number_of_frames: int


class ImageSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.IMAGE]


class AudioSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.AUDIO]
    duration_ms: int


SpaceInfo = Union[VideoSpaceInfo | AudioSpaceInfo]
