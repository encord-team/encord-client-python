"""Transport for native manual-work assignment operations."""

from typing import Sequence
from uuid import UUID

from encord.exceptions import ResourceExistsError
from encord.orm import tasks_v3 as dto
from encord.workflow_v3._client import WorkflowClient
from encord.workflow_v3.exceptions import StaleTaskError


def assign_task(
    client: WorkflowClient,
    task_id: UUID,
    *,
    assignee: str,
) -> None:
    try:
        client.api_client.post(
            f"projects/{client.project_id}/workflow-v3/tasks/{task_id}/assign",
            params=None,
            payload=dto.AssignTaskPayload(assignee=assignee),
            result_type=None,
            allow_none=True,
            allow_retries=False,
        )
    except ResourceExistsError as exc:
        raise StaleTaskError(
            f"Cannot assign task {task_id} in project {client.project_id}: {exc.message}",
            context=exc.context,
        ) from exc


def release_task(client: WorkflowClient, task_id: UUID) -> None:
    try:
        client.api_client.post(
            f"projects/{client.project_id}/workflow-v3/tasks/{task_id}/release",
            params=None,
            payload=None,
            result_type=None,
            allow_none=True,
            allow_retries=False,
        )
    except ResourceExistsError as exc:
        raise StaleTaskError(
            f"Cannot release task {task_id} in project {client.project_id}: {exc.message}",
            context=exc.context,
        ) from exc


def release_tasks(client: WorkflowClient, task_ids: Sequence[UUID]) -> None:
    if not task_ids:
        raise ValueError("Release at least one task.")
    try:
        client.api_client.post(
            f"projects/{client.project_id}/workflow-v3/tasks/release",
            params=None,
            payload=dto.ReleaseTasksPayload(task_ids=list(task_ids)),
            result_type=None,
            allow_none=True,
            allow_retries=False,
        )
    except ResourceExistsError as exc:
        raise StaleTaskError(
            f"Cannot release tasks in project {client.project_id}: {exc.message}",
            context=exc.context,
        ) from exc
