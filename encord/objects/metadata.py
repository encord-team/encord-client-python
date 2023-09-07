from typing import Optional

from encord.orm.base_dto import BaseDTO


class DICOMSeriesMetadata(BaseDTO):
    """
    Metadata for the DICOM series
    """

    patient_id: Optional[str]
    study_uid: str
    series_uid: str


class DICOMSliceMetadata(BaseDTO):
    """
    Metadata for a slice in a DICOM series
    """

    dicom_instance_uid: str
    multiframe_frame_number: Optional[int]
    file_uri: str
    width: int
    height: int
