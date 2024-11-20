from enum import Enum, auto
from typing import List, Optional, Union
from uuid import UUID

from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO


class DicomDeIdRedactTextMode(CamelStrEnum):
    REDACT_ALL_TEXT = auto()
    REDACT_NO_TEXT = auto()
    REDACT_SENSITIVE_TEXT = auto()


class DicomDeIdSaveConditionType(CamelStrEnum):
    NOT_SUBSTR = auto()
    IN = auto()


class DicomDeIdSaveCondition(BaseDTO):
    value: Union[str, List[str]]
    condition_type: DicomDeIdSaveConditionType
    dicom_tag: str


class DicomDeIdStartPayload(BaseDTO):
    integration_uuid: UUID
    dicom_urls: List[str]
    redact_dicom_tags: bool = True
    redact_pixels_mode: DicomDeIdRedactTextMode = DicomDeIdRedactTextMode.REDACT_NO_TEXT
    save_conditions: Optional[List[DicomDeIdSaveCondition]] = None
    upload_dir: Optional[str] = None


class DicomDeIdGetResultParams(BaseDTO):
    timeout_seconds: int


class DicomDeIdGetResultLongPollingStatus(str, Enum):
    DONE = "DONE"
    ERROR = "ERROR"
    PENDING = "PENDING"


class DicomDeIdGetResultResponse(BaseDTO):
    status: DicomDeIdGetResultLongPollingStatus
    urls: Optional[List[str]] = None
