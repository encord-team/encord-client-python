"""Transport and response conversion for native task reads."""

from datetime import datetime
from typing import Dict, Iterator, Optional, Sequence, Type, TypedDict, Union
from uuid import UUID

from encord.beta.workflow_v3 import tasks
from encord.beta.workflow_v3._client import WorkflowClient
from encord.orm import tasks_v3 as dto
from encord.orm.tasks_v3 import TaskSort, TaskStatus
from encord.orm.workflow_v3 import StageType

_TASK_CLASS_BY_STAGE_TYPE: Dict[StageType, Type[tasks.Task]] = {
    StageType.EXTERNAL: tasks.ExternalTask,
    StageType.ANNOTATION: tasks.AnnotationTask,
    StageType.REVIEW: tasks.ReviewTask,
}


class _TargetArguments(TypedDict):
    _client: WorkflowClient
    id: UUID
    project_id: UUID
    dataset_hash: str
    created_at: datetime
    deleted_at: Optional[datetime]


def _target(client: WorkflowClient, target: dto.TaskTargetDTO) -> tasks.TaskTarget:
    common: _TargetArguments = {
        "_client": client,
        "id": target.id,
        "project_id": target.project_id,
        "dataset_hash": target.dataset_hash,
        "created_at": target.created_at,
        "deleted_at": target.deleted_at,
    }
    if isinstance(target, dto.DataUnitTargetDTO):
        return tasks.DataUnitTarget(**common, data_hash=target.data_hash)
    elif isinstance(target, dto.DataUnitSliceTargetDTO):
        return tasks.DataUnitSliceTarget(**common, data_hash=target.data_hash, qualifier_name=target.qualifier_name)
    elif isinstance(target, dto.DatasetTargetDTO):
        return tasks.DatasetTarget(**common)
    elif isinstance(target, dto.DataGroupSubsetTargetDTO):
        return tasks.DataGroupSubsetTarget(**common, data_hash=target.data_hash, qualifier_name=target.qualifier_name)
    elif isinstance(target, dto.DatasetSubsetTargetDTO):
        return tasks.DatasetSubsetTarget(**common, qualifier_name=target.qualifier_name)
    else:
        return tasks.UnknownTarget(**common, raw_target_type=target.target_type)


def _construct(client: WorkflowClient, record: dto.TaskDTO) -> tasks.Task:
    assignment = record.assignment
    stage_type = StageType(record.stage_type)
    task_class = _TASK_CLASS_BY_STAGE_TYPE.get(stage_type, tasks.Task)
    return task_class(
        _client=client,
        id=record.id,
        stage_id=record.stage_id,
        stage_type=stage_type,
        target=_target(client, record.target),
        status=record.status,
        priority=record.priority,
        created_at=record.created_at,
        entered_at=record.entered_at,
        processing_at=record.processing_at,
        done_at=record.done_at,
        canceled_at=record.canceled_at,
        raw_stage_type=record.stage_type if stage_type is StageType.UNKNOWN else None,
        assignment=None
        if assignment is None
        else tasks.Assignment(
            assignment.assigned_to,
            assignment.assigned_by,
            assignment.assigned_at,
        ),
    )


def list_tasks(
    client: WorkflowClient,
    stage_id: UUID,
    *,
    statuses: Optional[Sequence[TaskStatus]] = None,
    sort: Optional[TaskSort] = None,
) -> Iterator[tasks.Task]:
    if statuses is not None and any(
        not isinstance(status, TaskStatus) or status is TaskStatus.UNKNOWN for status in statuses
    ):
        raise ValueError("statuses must contain known TaskStatus values.")
    if sort is not None and not isinstance(sort, TaskSort):
        raise ValueError("sort must be a TaskSort value.")
    params = dto.TasksQueryParams(statuses=None if statuses is None else list(statuses), sort=sort)
    return (
        _construct(client, record)
        for record in client.api_client.get_paged_iterator(
            f"projects/{client.project_id}/workflow-v3/stages/{stage_id}/tasks",
            params=params,
            result_type=dto.TaskDTO,
        )
    )


def get_task(client: WorkflowClient, id: Union[UUID, str]) -> tasks.Task:
    try:
        task_id = id if isinstance(id, UUID) else UUID(id)
    except ValueError as error:
        raise ValueError(f"Invalid task ID: {id!r}.") from error
    record = client.api_client.get(
        f"projects/{client.project_id}/workflow-v3/tasks/{task_id}", params=None, result_type=dto.TaskDTO
    )
    return _construct(client, record)
