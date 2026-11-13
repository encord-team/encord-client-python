"""Transport for native task submission."""

from typing import Optional, Sequence, Union
from uuid import UUID

from encord.beta.workflow_v3._client import WorkflowClient
from encord.beta.workflow_v3._pathway_selector import build_pathway_selector
from encord.beta.workflow_v3.exceptions import StaleTaskError
from encord.exceptions import ResourceExistsError, ResourceNotFoundError
from encord.orm.tasks_v3 import SubmitTaskPayload, SubmitTasksPayload


def submit_task(
    client: WorkflowClient,
    task_id: UUID,
    *,
    pathway_id: Optional[Union[UUID, str]],
    pathway_name: Optional[str],
    comment: Optional[str] = None,
) -> None:
    pathway = build_pathway_selector(pathway_id, pathway_name)
    try:
        client.api_client.post(
            f"projects/{client.project_id}/workflow-v3/tasks/{task_id}/submit",
            params=None,
            payload=SubmitTaskPayload(pathway=pathway, comment=comment),
            result_type=None,
            allow_none=True,
            allow_retries=False,
        )
    except ResourceExistsError as exc:
        raise StaleTaskError(
            f"Cannot submit task {task_id} in project {client.project_id}: {exc.message}",
            context=exc.context,
        ) from exc


def submit_tasks(
    client: WorkflowClient,
    stage_id: UUID,
    task_ids: Sequence[UUID],
    *,
    pathway_id: Optional[Union[UUID, str]],
    pathway_name: Optional[str],
    comment: Optional[str] = None,
) -> None:
    if not 1 <= len(task_ids) <= 100:
        raise ValueError("Submit between 1 and 100 tasks.")
    payload = SubmitTasksPayload(
        task_ids=list(task_ids),
        pathway=build_pathway_selector(pathway_id, pathway_name),
        comment=comment,
    )
    try:
        client.api_client.post(
            f"projects/{client.project_id}/workflow-v3/stages/{stage_id}/tasks/submit",
            params=None,
            payload=payload,
            result_type=None,
            allow_none=True,
            allow_retries=False,
        )
    except ResourceExistsError as exc:
        raise StaleTaskError(
            f"Cannot submit tasks at stage {stage_id} in project {client.project_id}: {exc.message}",
            context=exc.context,
        ) from exc
    except ResourceNotFoundError as exc:
        raise ResourceNotFoundError(
            f"Cannot submit tasks at stage {stage_id} in project {client.project_id}: {exc.message}",
            context=exc.context,
        ) from exc
