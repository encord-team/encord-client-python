from typing import TypedDict

from encord.constants.enums import DataType, SpaceType


class LabelBlob(TypedDict):
    objects: list[dict]
    classifications: list[dict]


class SpaceInfo(TypedDict):
    space_type: SpaceType
    data_type: DataType
    labels: dict[str, LabelBlob]
