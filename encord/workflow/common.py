from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple, Type, TypeVar
from uuid import UUID

from encord.http.bundle import Bundle, bundled_operation
from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO, PrivateAttr


class TasksQueryParams(BaseDTO):
    page_token: Optional[str] = None


@dataclass(frozen=True)
class WorkflowStageBase:
    _workflow_client: WorkflowClient
    uuid: UUID
    title: str

    def __repr__(self):
        return f"{self.__class__.__name__}(stage_type={self.stage_type}, uuid='{self.uuid}', title='{self.title}')"


class WorkflowTask(BaseDTO):
    _stage_uuid: Optional[UUID] = PrivateAttr(None)
    _workflow_client: Optional[WorkflowClient] = PrivateAttr(None)

    uuid: UUID
    created_at: datetime
    updated_at: datetime

    def _get_client_data(self) -> Tuple[WorkflowClient, UUID]:
        assert self._stage_uuid
        assert self._workflow_client
        return self._workflow_client, self._stage_uuid


class WorkflowAction(BaseDTO):
    task_uuid: UUID


TaskT = TypeVar("TaskT", bound=WorkflowTask)
ReviewT = TypeVar("ReviewT", bound=BaseDTO)


@dataclass
class BundledWorkflowActionPayload:
    stage_uuid: UUID
    actions: list[WorkflowAction]

    def add(self, other: BundledWorkflowActionPayload) -> BundledWorkflowActionPayload:
        assert self.stage_uuid == other.stage_uuid, "It's only possible to bundle actions for one stage at a time"
        self.actions.extend(other.actions)
        return self


class WorkflowReviewAction(BaseDTO):
    review_uuid: UUID


@dataclass
class BundledReviewActionPayload:
    stage_uuid: UUID
    task_uuid: UUID
    actions: list[WorkflowReviewAction]

    def add(self, other: BundledReviewActionPayload) -> BundledReviewActionPayload:
        assert self.stage_uuid == other.stage_uuid, "It's only possible to bundle actions for one stage at a time"
        assert self.task_uuid == other.task_uuid, "It's only possible to bundle review actions one task at a time"
        self.actions.extend(other.actions)
        return self


@dataclass
class WorkflowClient:
    api_client: ApiClient
    project_hash: UUID

    def get_tasks(self, stage_uuid: UUID, params: TasksQueryParams, type_: Type[TaskT]) -> Iterable[TaskT]:
        return self.api_client.get_paged_iterator(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/tasks",
            params=params,
            result_type=type_,
        )

    def action(self, stage_uuid: UUID, action: WorkflowAction, *, bundle: Optional[Bundle] = None) -> None:
        if not bundle:
            self._action(stage_uuid, [action])
        else:
            bundled_operation(
                bundle=bundle,
                operation=self._action,
                payload=BundledWorkflowActionPayload(stage_uuid=stage_uuid, actions=[action]),
            )

    def _action(self, stage_uuid: UUID, actions: Sequence[WorkflowAction]) -> None:
        self.api_client.post(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/actions",
            params=None,
            payload=actions,
            result_type=None,
        )

    def get_label_reviews(self, stage_uuid: UUID, task_uuid: UUID, type_: Type[ReviewT]) -> Iterable[ReviewT]:
        return self.api_client.get_paged_iterator(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/tasks/{task_uuid}/reviews",
            params=TasksQueryParams(),
            result_type=type_,
        )

    def label_review_action(
        self,
        stage_uuid: UUID,
        task_uuid: UUID,
        action: WorkflowReviewAction,
        *,
        bundle: Optional[Bundle] = None,
    ) -> None:
        if not bundle:
            self._label_review_action(stage_uuid, task_uuid, [action])
        else:
            bundled_operation(
                bundle=bundle,
                operation=self._label_review_action,
                payload=BundledReviewActionPayload(stage_uuid=stage_uuid, task_uuid=task_uuid, actions=[action]),
            )

    def _label_review_action(self, stage_uuid: UUID, task_uuid: UUID, actions: Sequence[WorkflowReviewAction]) -> None:
        self.api_client.post(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/tasks/{task_uuid}/reviews/actions",
            params=TasksQueryParams(),
            payload=actions,
            result_type=None,
        )
