from typing import Optional

from encord.orm.base_dto import BaseDTO


class DicomSeriesMetadata(BaseDTO):
    patient_id: Optional[str]
    study_uid: str
    series_uid: str


class DicomAnnotationData(BaseDTO):
    dicom_instance_uid: str
    multiframe_frame_number: Optional[int]
    file_uri: str
    width: int
    height: int
