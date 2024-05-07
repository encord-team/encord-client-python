from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Tuple, Type, TypeVar
from uuid import UUID

from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO


class TasksQueryParams(BaseDTO):
    page_token: Optional[str] = None


@dataclass(frozen=True)
class WorkflowStageBase:
    workflow_client: WorkflowClient
    uuid: UUID
    title: str

    def __repr__(self):
        return f"{self.__class__.__name__}(stage_type={self.stage_type}, uuid='{self.uuid}', title='{self.title}')"


class WorkflowTask(BaseDTO):
    _stage_uuid: Optional[UUID] = None
    _workflow_client: Optional[WorkflowClient] = None

    uuid: UUID
    created_at: datetime
    updated_at: datetime

    def _get_client_data(self) -> Tuple[WorkflowClient, UUID]:
        assert self._stage_uuid
        assert self._workflow_client
        return self._workflow_client, self._stage_uuid


class WorkflowAction(BaseDTO):
    task_uuid: UUID


T = TypeVar("T", bound=WorkflowTask)


@dataclass
class WorkflowClient:
    api_client: ApiClient
    project_hash: UUID

    def get_tasks(self, stage_uuid: UUID, type_: Type[T]) -> Iterable[T]:
        return self.api_client.get_paged_iterator(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/tasks",
            params=TasksQueryParams(),
            result_type=type_,
        )

    def action(self, stage_uuid: UUID, action: WorkflowAction) -> None:
        self.api_client.post(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/actions",
            params=None,
            payload=[action],
            result_type=None,
        )
