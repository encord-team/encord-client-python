from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Iterable, Literal, Optional, Type, TypeVar
from uuid import UUID

from typing_extensions import Annotated

from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO, Field
from encord.orm.workflow import Workflow as WorkflowORM
from encord.orm.workflow import WorkflowNode, WorkflowStageType


class WorkflowTask(BaseDTO):
    uuid: UUID
    created_at: datetime
    updated_at: datetime


class WorkflowAction(BaseDTO):
    task_uuid: UUID


class AnnotationTask(WorkflowTask):
    assignee: str | None
    label_branch_name: str
    data_hash: UUID
    data_title: str
    subtasks: list[AnnotationTask] = Field(default_factory=list)

    class _ActionSubmit(WorkflowAction):
        action: Literal["submit"] = "submit"

    class _ActionAssign(WorkflowAction):
        action: Literal["assign"] = "assign"
        assignee: str

    class _ActionRelease(WorkflowAction):
        action: Literal["release"] = "release"

    def submit(self) -> None:
        self._workflow_client.action(AnnotationTask._ActionSubmit(task_uuid=self.uuid))

    def assign(self, assignee: str) -> None:
        self._workflow_client.action(AnnotationTask._ActionAssign(task_uuid=self.uuid, assignee=assignee))

    def release(self) -> None:
        self._workflow_client.action(AnnotationTask._ActionRelease(task_uuid=self.uuid))


class ReviewTask(WorkflowTask):
    assignee: str | None
    label_branch_name: str
    data_hash: UUID
    data_title: str


class ConsensusReviewTask(WorkflowTask):
    assignee: str | None
    data_hash: UUID
    data_title: str


class TasksQueryParams(BaseDTO):
    page_token: Optional[str] = None


T = TypeVar("T")


class _WorkflowActionsPayload(BaseDTO):
    actions: list[WorkflowAction]


@dataclass
class WorkflowClient:
    api_client: ApiClient
    project_hash: UUID

    def get_tasks(self, stage_uuid: UUID, type_=Type[T]) -> Iterable[T]:
        return self.api_client.get_paged_iterator(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/tasks",
            params=TasksQueryParams(),
            result_type=type_,
        )

    def action(self, stage_uuid: UUID, action: WorkflowAction) -> None:
        self.api_client.post(
            path=f"/projects/{self.project_hash}/workflow/stages/{stage_uuid}/actions",
            params=None,
            payload=_WorkflowActionsPayload(actions=[action]),
            result_type=None,
        )


@dataclass(frozen=True)
class WorkflowStageBase:
    workflow_client: WorkflowClient
    uuid: UUID
    title: str

    def __repr__(self):
        return f"{self.__class__.__name__}(stage_type={self.stage_type}, uuid='{self.uuid}', title='{self.title}')"


class AnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.ANNOTATION] = WorkflowStageType.ANNOTATION

    def get_tasks(self) -> Iterable[AnnotationTask]:
        yield from self.workflow_client.get_tasks(self.uuid, type_=AnnotationTask)


class ConsensusAnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_ANNOTATION] = WorkflowStageType.CONSENSUS_ANNOTATION

    def get_tasks(self) -> Iterable[AnnotationTask]:
        yield from self.workflow_client.get_tasks(self.uuid, type_=AnnotationTask)


class ReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.REVIEW] = WorkflowStageType.REVIEW

    def get_tasks(self) -> Iterable[ReviewTask]:
        yield from self.workflow_client.get_tasks(self.uuid, type_=ReviewTask)


class ConsensusReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_REVIEW] = WorkflowStageType.CONSENSUS_REVIEW

    def get_tasks(self) -> Iterable[ConsensusReviewTask]:
        yield from self.workflow_client.get_tasks(self.uuid, type_=ConsensusReviewTask)


class FinalStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.DONE] = WorkflowStageType.DONE

    def get_tasks(self) -> Iterable[ConsensusReviewTask]:
        yield from self.workflow_client.get_tasks(self.uuid, type_=FinalStage)


WorkflowStage = Annotated[
    AnnotationStage | ReviewStage | ConsensusAnnotationStage | ConsensusReviewStage | FinalStage,
    Field(discriminator="stage_type"),
]


def _construct_stage(workflow_client: WorkflowClient, node: WorkflowNode) -> WorkflowStage:
    match node.stage_type:
        case WorkflowStageType.ANNOTATION:
            return AnnotationStage(uuid=node.uuid, title=node.title, workflow_client=workflow_client)
        case WorkflowStageType.REVIEW:
            return ReviewStage(uuid=node.uuid, title=node.title, workflow_client=workflow_client)
        case WorkflowStageType.CONSENSUS_ANNOTATION:
            return ConsensusAnnotationStage(uuid=node.uuid, title=node.title, workflow_client=workflow_client)
        case WorkflowStageType.CONSENSUS_REVIEW:
            return ConsensusReviewStage(uuid=node.uuid, title=node.title, workflow_client=workflow_client)
        case WorkflowStageType.DONE:
            return FinalStage(uuid=node.uuid, title=node.title, workflow_client=workflow_client)
        case _:
            raise AssertionError(f"Unknown stage type: {node.stage_type}")


class Workflow:
    stages: list[WorkflowStage] = []

    def __init__(self, api_client: ApiClient, project_hash: UUID, workflow_orm: WorkflowORM):
        workflow_client = WorkflowClient(api_client, project_hash)

        self.stages = [_construct_stage(workflow_client, x) for x in workflow_orm.stages]

    def get_stage(self, *, name: str | None = None, uuid: UUID | None = None) -> WorkflowStage:
        for stage in self.stages:
            if (uuid is not None and stage.uuid == uuid) or (name is not None and stage.title == name):
                return stage

        raise ValueError(f"No matching stage found: '{uuid or name}'")
