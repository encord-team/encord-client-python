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

from typing import Any

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
    DataType.DICOM,
    DataType.DICOM_STUDY,
    DataType.NIFTI,
}


def is_geometric(data_type: DataType) -> bool:
    return data_type in GEOMETRIC_TYPES
