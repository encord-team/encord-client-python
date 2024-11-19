from enum import Enum, auto
from typing import List
from uuid import UUID

from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO


class PublicDicomDeIdRedactTextMode(CamelStrEnum):
    REDACT_ALL_TEXT = auto()
    REDACT_NO_TEXT = auto()
    REDACT_SENSITIVE_TEXT = auto()


class PublicDicomDeIdSaveConditionType(CamelStrEnum):
    NOT_SUBSTR = auto()
    IN = auto()


class PublicDicomDeIdSaveCondition(BaseDTO):
    value: str | List[str]
    condition_type: PublicDicomDeIdSaveConditionType
    dicom_tag: str


class PublicDicomDeIdStartPayload(BaseDTO):
    integration_uuid: UUID
    dicom_urls: List[str]
    redact_dicom_tags: bool = True
    redact_pixels_mode: PublicDicomDeIdRedactTextMode = PublicDicomDeIdRedactTextMode.REDACT_NO_TEXT
    save_conditions: list[PublicDicomDeIdSaveCondition] | None = None
    upload_dir: str | None = None


class PublicDicomDeIdGetResultParams(BaseDTO):
    timeout_seconds: int


class PublicDicomDeIdGetResultLongPollingStatus(str, Enum):
    DONE = "DONE"
    ERROR = "ERROR"
    PENDING = "PENDING"


class PublicDicomDeIdGetResultResponse(BaseDTO):
    status: PublicDicomDeIdGetResultLongPollingStatus
    urls: List[str] | None = None
