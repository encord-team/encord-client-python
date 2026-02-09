from __future__ import annotations

from datetime import datetime
from enum import auto
from uuid import UUID

from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO


class TaskActionType(CamelStrEnum):
    """Task action event types from workflow_task_events_v2 table."""

    ASSIGN = auto()
    APPROVE = auto()
    SUBMIT = auto()
    MOVE = auto()
    REJECT = auto()
    RELEASE = auto()
    SKIP = auto()


class TaskAction(BaseDTO):
    """Task action event returned by the task actions endpoint."""

    timestamp: datetime
    action_type: TaskActionType
    project_uuid: UUID
    workflow_stage_uuid: UUID
    task_uuid: UUID
    data_unit_uuid: UUID
    actor_email: str
