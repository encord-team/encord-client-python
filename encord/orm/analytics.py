from datetime import datetime
from enum import Enum, auto
from typing import List, Literal, Optional
from uuid import UUID

from encord.common.utils import snake_to_camel
from encord.orm.base_dto import BaseDTO
from encord.orm.workflow import WorkflowNode, WorkflowStageType
from encord.utilities.project_user import ProjectUserRole


class CamelStrEnum(str, Enum):
    # noinspection PyMethodParameters
    def _generate_next_value_(name, start, count, last_values) -> str:  # type: ignore
        return snake_to_camel(name)


class CollaboratorTimersGroupBy(CamelStrEnum):
    DATA_UNIT = auto()
    PROJECT = auto()


class CollaboratorTimerParams(BaseDTO):
    project_hash: str
    after: datetime
    before: Optional[datetime] = None
    group_by: CollaboratorTimersGroupBy = CollaboratorTimersGroupBy.DATA_UNIT
    page_size: int = 100
    page_token: Optional[str] = None


class CollaboratorTimer(BaseDTO):
    user_email: str
    user_role: ProjectUserRole
    data_title: Optional[str] = None
    time_seconds: float


class TimeSpentParams(BaseDTO):
    project_uuid: str
    after: datetime
    before: Optional[datetime] = None
    workflow_stage_uuids: Optional[List[UUID]] = None
    user_emails: Optional[List[str]] = None
    dataset_uuids: Optional[List[UUID]] = None
    data_uuids: Optional[List[UUID]] = None
    data_title: Optional[str] = None
    page_token: Optional[str] = None


class TimeSpent(BaseDTO):
    period_start_time: datetime
    period_end_time: datetime
    time_spent_seconds: int
    user_email: str
    project_user_role: ProjectUserRole
    data_uuid: UUID
    data_title: str
    dataset_uuid: UUID
    dataset_title: str
    workflow_task_uuid: Optional[UUID] = None
    workflow_stage: WorkflowNode
