from __future__ import annotations

from datetime import datetime
from enum import auto
from typing import Iterable, List, Optional, Union
from uuid import UUID

from encord.http.v2.api_client import ApiClient
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


class _GetTaskActionsParams(BaseDTO):
    """Parameters for get_task_actions API call."""

    project_uuid: UUID
    after: datetime
    before: datetime
    actor_email: Optional[List[str]] = None
    action_type: Optional[List[TaskActionType]] = None
    workflow_stage_uuid: Optional[List[UUID]] = None
    data_unit_uuid: Optional[List[UUID]] = None


class _TaskActionsClient:
    def __init__(self, api_client: ApiClient) -> None:
        self._api_client = api_client

    def get_task_actions(
        self,
        *,
        project_uuid: UUID,
        after: datetime,
        before: Optional[datetime] = None,
        actor_email: Union[str, List[str], None] = None,
        action_type: Union[TaskActionType, List[TaskActionType], None] = None,
        workflow_stage_uuid: Union[UUID, List[UUID], None] = None,
        data_unit_uuid: Union[UUID, List[UUID], None] = None,
    ) -> Iterable[TaskAction]:
        """
        Get task actions with automatic pagination.

        Normalizes single values to lists and uses current time for before if not provided.
        """
        # Normalize single values to lists
        actor_emails = self._normalize_to_list(actor_email)
        action_types = self._normalize_to_list(action_type)
        workflow_stage_uuids = self._normalize_to_list(workflow_stage_uuid)
        data_unit_uuids = self._normalize_to_list(data_unit_uuid)

        # Use current time for before if not provided
        if before is None:
            before = datetime.utcnow()

        params = _GetTaskActionsParams(
            project_uuid=project_uuid,
            after=after,
            before=before,
            actor_email=actor_emails,
            action_type=action_types,
            workflow_stage_uuid=workflow_stage_uuids,
            data_unit_uuid=data_unit_uuids,
        )

        return self._api_client.get_paged_iterator(
            path=f"/projects/{project_uuid}/analytics/task-actions",
            params=params,
            result_type=TaskAction,  # type: ignore[arg-type]
        )

    @staticmethod
    def _normalize_to_list(value: Union[str, int, UUID, TaskActionType, List, None]) -> Optional[List]:
        """Convert single value or list to list, or return None."""
        if value is None:
            return None
        if isinstance(value, list):
            return value
        return [value]
