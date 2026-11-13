"""Internal wire models for native task reads and actions."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional, Union
from uuid import UUID

from encord.orm.base_dto import BaseDTO, BaseDTOWithExtra, Field, dto_validator
from encord.orm.workflow_v3 import ReadEnum


class TaskStatus(ReadEnum):
    """Task lifecycle; assignment and action eligibility are separate concerns."""

    ENTERING = "entering"
    ENTERED = "entered"
    PROCESSING = "processing"
    PROCESSING_FAILED = "processingFailed"
    ENTERING_FAILED = "enteringFailed"
    DONE = "done"
    CANCELED = "cancelled"
    UNKNOWN = "_UNKNOWN_"


class TaskSort(str, Enum):
    """Supported live-work ordering; terminal stages use newest arrival first."""

    PRIORITY = "priority"
    CREATED_AT = "createdAt"


class TargetDTO(BaseDTO):
    id: UUID
    project_id: UUID
    dataset_hash: str = Field(alias="datasetId")
    created_at: datetime
    deleted_at: Optional[datetime] = None


class DataUnitTargetDTO(TargetDTO):
    target_type: Literal["data_unit"]
    data_hash: str = Field(alias="dataId")


class DataUnitSliceTargetDTO(TargetDTO):
    target_type: Literal["data_unit_slice"]
    data_hash: str = Field(alias="dataId")
    qualifier_name: str


class DatasetTargetDTO(TargetDTO):
    target_type: Literal["dataset"]


class DataGroupSubsetTargetDTO(TargetDTO):
    target_type: Literal["data_group_subset"]
    data_hash: str = Field(alias="dataId")
    qualifier_name: str


class DatasetSubsetTargetDTO(TargetDTO):
    target_type: Literal["dataset_subset"]
    qualifier_name: str


class UnknownTargetDTO(TargetDTO, BaseDTOWithExtra):
    target_type: str

    @dto_validator(mode="before")
    @classmethod
    def require_unfamiliar_type(cls, values: Any) -> Any:
        if isinstance(values, cls):
            return values
        target_type = values.get("targetType", values.get("target_type")) if isinstance(values, dict) else None
        if not isinstance(target_type, str) or target_type in {
            "data_unit",
            "data_unit_slice",
            "dataset",
            "data_group_subset",
            "dataset_subset",
        }:
            raise ValueError("Expected an unfamiliar target type.")
        return values


TaskTargetDTO = Union[
    DataUnitTargetDTO,
    DataUnitSliceTargetDTO,
    DatasetTargetDTO,
    DataGroupSubsetTargetDTO,
    DatasetSubsetTargetDTO,
    UnknownTargetDTO,
]


class AssignmentDTO(BaseDTO):
    assigned_to: Optional[str] = None
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None


class TaskDTO(BaseDTO):
    id: UUID
    stage_id: UUID
    stage_type: str
    target: TaskTargetDTO
    status: TaskStatus
    priority: float
    created_at: datetime
    entered_at: Optional[datetime] = None
    processing_at: Optional[datetime] = None
    done_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = Field(default=None, alias="cancelledAt")
    assignment: Optional[AssignmentDTO] = None


class TasksQueryParams(BaseDTO):
    page_token: Optional[str] = None
    sort: Optional[TaskSort] = None
    statuses: Optional[list[TaskStatus]] = None


class PathwayById(BaseDTO):
    id: UUID


class PathwayByName(BaseDTO):
    name: str


class SubmitTaskPayload(BaseDTO):
    pathway: Optional[Union[PathwayById, PathwayByName]] = None
    comment: Optional[str] = None


class SubmitTasksPayload(SubmitTaskPayload):
    task_ids: list[UUID]


class AssignTaskPayload(BaseDTO):
    assignee: str


class ReleaseTasksPayload(BaseDTO):
    task_ids: list[UUID]
