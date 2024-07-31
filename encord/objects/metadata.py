"""
---
title: "Objects - DICOM Metadata"
slug: "sdk-ref-objects-dicom-metadata"
hidden: false
metadata:
  title: "Objects - DICOM Metadata"
  description: "Encord SDK Objects - DICOM Metadata."
category: "64e481b57b6027003f20aaa0"
---
"""

from typing import Optional

from encord.orm.base_dto import BaseDTO


class DICOMSeriesMetadata(BaseDTO):
    """
    Metadata for a DICOM series.

    Attributes:
        patient_id (Optional[str]): The ID of the patient. This attribute is optional.
        study_uid (str): The unique identifier for the study.
        series_uid (str): The unique identifier for the series.
    """

    patient_id: Optional[str]
    study_uid: str
    series_uid: str


class DICOMSliceMetadata(BaseDTO):
    """
    Metadata for a slice in a DICOM series.

    Attributes:
        dicom_instance_uid (str): The unique identifier for the DICOM instance.
        multiframe_frame_number (Optional[int]): The frame number if the DICOM instance is a multiframe image. This attribute is optional.
        file_uri (str): The URI to the file containing the slice.
        width (int): The width of the slice in pixels.
        height (int): The height of the slice in pixels.
    """

    dicom_instance_uid: str
    multiframe_frame_number: Optional[int]
    file_uri: str
    width: int
    height: int
