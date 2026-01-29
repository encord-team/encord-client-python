"""---
title: "Enums"
slug: "sdk-ref-enums"
hidden: false
metadata:
  title: "Enums"
  description: "Encord SDK Enums."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from typing import Any, Set

from encord.common.enum import StringEnum


class DataType(StringEnum):
    VIDEO = "video"
    IMG_GROUP = "img_group"
    DICOM = "dicom"
    IMAGE = "image"
    DICOM_STUDY = "dicom_study"
    NIFTI = "nifti"
    AUDIO = "audio"
    PLAIN_TEXT = "plain_text"
    PDF = "pdf"
    GROUP = "group"
    SCENE = "scene"

    # will be displayed if the Encord platform has a new data type that is not present in this SDK version. Please upgrade your SDK version
    MISSING_DATA_TYPE = "_MISSING_DATA_TYPE_"

    @classmethod
    def _missing_(cls, value: Any) -> DataType:
        return cls.MISSING_DATA_TYPE

    @staticmethod
    def from_upper_case_string(string: str) -> DataType:
        for data_type in DataType:
            if string == data_type.to_upper_case_string():
                return data_type

        return DataType.MISSING_DATA_TYPE

    def to_upper_case_string(self) -> str:
        return self.value.upper()


GEOMETRIC_TYPES = {
    DataType.VIDEO,
    DataType.IMAGE,
    DataType.IMG_GROUP,
    DataType.GROUP,
    DataType.DICOM,
    DataType.DICOM_STUDY,
    DataType.NIFTI,
    DataType.PDF,
    DataType.SCENE,
}


def is_geometric(data_type: DataType) -> bool:
    return data_type in GEOMETRIC_TYPES


# When adding a new space, it is recommended to use mypy immediately after to check for places to update.
class SpaceType(StringEnum):
    VIDEO = "video"
    IMAGE = "image"
    MULTILAYER_IMAGE = "multilayer_image"
    IMAGE_SEQUENCE = "image_sequence"
    AUDIO = "audio"
    TEXT = "text"
    HTML = "html"
    MEDICAL_FILE = "medical_file"
    MEDICAL_STACK = "medical_stack"
    SCENE_IMAGE = "scene_image"
    POINT_CLOUD = "point_cloud"
    PDF = "pdf"


DATA_TYPES_WITH_UNKNOWN_LAST_FRAME: Set[DataType] = {
    DataType.DICOM,
    DataType.SCENE,  # Scene duration is currently unknown
}
