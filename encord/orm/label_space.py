from typing import Literal, TypedDict, Union

from encord.constants.enums import DataType, SpaceType


class LabelBlob(TypedDict):
    objects: list[dict]
    classifications: list[dict]


class BaseSpaceInfo(TypedDict):
    space_type: SpaceType
    labels: dict[str, LabelBlob]


class VideoSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.VISION]
    number_of_frames: int


class AudioSpaceInfo(BaseSpaceInfo):
    space_type: Literal[SpaceType.AUDIO]
    duration_ms: int


SpaceInfo = Union[VideoSpaceInfo | AudioSpaceInfo]
