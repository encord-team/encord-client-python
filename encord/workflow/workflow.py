from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Iterable, Literal, Optional, Tuple, Type, TypeVar, Union
from uuid import UUID

from typing_extensions import Annotated

from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO, BaseDTOInterface, Field
from encord.orm.workflow import Workflow as WorkflowORM
from encord.orm.workflow import WorkflowNode, WorkflowStageType


class WorkflowAction(BaseDTO):
    task_uuid: UUID


class WorkflowTask(BaseDTO):
    _stage_uuid: UUID | None = None
    _workflow_client: WorkflowClient | None = None

    uuid: UUID
    created_at: datetime
    updated_at: datetime

    def _get_client_data(self) -> Tuple[WorkflowClient, UUID]:
        assert self._stage_uuid
        assert self._workflow_client
        return self._workflow_client, self._stage_uuid


class ConsensusAnnotationTask(WorkflowTask):
    data_hash: UUID
    data_title: str
    subtasks: list[AnnotationTask] = Field(default_factory=list)


class AnnotationTask(WorkflowTask):
    assignee: str | None
    label_branch_name: str

    class _ActionSubmit(WorkflowAction):
        action: Literal["SUBMIT"] = "SUBMIT"

    class _ActionAssign(WorkflowAction):
        action: Literal["ASSIGN"] = "ASSIGN"
        assignee: str

    class _ActionRelease(WorkflowAction):
        action: Literal["RELEASE"] = "RELEASE"

    def submit(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, AnnotationTask._ActionSubmit(task_uuid=self.uuid))

    def assign(self, assignee: str) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, AnnotationTask._ActionAssign(task_uuid=self.uuid, assignee=assignee))

    def release(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, AnnotationTask._ActionRelease(task_uuid=self.uuid))


class ReviewTask(WorkflowTask):
    assignee: str | None
    data_hash: UUID
    data_title: str

    class _ActionApprove(WorkflowAction):
        action: Literal["APPROVE"] = "APPROVE"

    class _ActionReject(WorkflowAction):
        action: Literal["REJECT"] = "REJECT"

    class _ActionAssign(WorkflowAction):
        action: Literal["ASSIGN"] = "ASSIGN"
        assignee: str

    class _ActionRelease(WorkflowAction):
        action: Literal["RELEASE"] = "RELEASE"

    def approve(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, ReviewTask._ActionApprove(task_uuid=self.uuid))

    def reject(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, ReviewTask._ActionReject(task_uuid=self.uuid))

    def assign(self, assignee: str) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, ReviewTask._ActionAssign(task_uuid=self.uuid, assignee=assignee))

    def release(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, ReviewTask._ActionRelease(task_uuid=self.uuid))


class ConsensusReviewOption(BaseDTO):
    annotator: str
    label_branch_name: str


class ConsensusReviewTask(WorkflowTask):
    assignee: str | None
    data_hash: UUID
    data_title: str
    options: list[ConsensusReviewOption]

    class _ActionApprove(WorkflowAction):
        action: Literal["APPROVE"] = "APPROVE"

    class _ActionReject(WorkflowAction):
        action: Literal["REJECT"] = "REJECT"

    class _ActionAssign(WorkflowAction):
        action: Literal["ASSIGN"] = "ASSIGN"
        assignee: str

    class _ActionRelease(WorkflowAction):
        action: Literal["RELEASE"] = "RELEASE"

    def approve(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, ConsensusReviewTask._ActionApprove(task_uuid=self.uuid))

    def reject(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, ConsensusReviewTask._ActionReject(task_uuid=self.uuid))

    def assign(self, assignee: str) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, ConsensusReviewTask._ActionAssign(task_uuid=self.uuid, assignee=assignee))

    def release(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, ConsensusReviewTask._ActionRelease(task_uuid=self.uuid))


class FinalStageTask(WorkflowTask):
    data_hash: UUID
    data_title: str


class TasksQueryParams(BaseDTO):
    page_token: Optional[str] = None


T = TypeVar("T", bound=WorkflowTask)


class _WorkflowActionsPayload(BaseDTO):
    actions: list[WorkflowAction]


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
        for task in self.workflow_client.get_tasks(self.uuid, type_=AnnotationTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self.workflow_client
            yield task


class ConsensusAnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_ANNOTATION] = WorkflowStageType.CONSENSUS_ANNOTATION

    def get_tasks(self) -> Iterable[ConsensusAnnotationTask]:
        for task in self.workflow_client.get_tasks(self.uuid, type_=ConsensusAnnotationTask):
            for subtask in task.subtasks:
                subtask._stage_uuid = self.uuid
                subtask._workflow_client = self.workflow_client

            yield task


class ReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.REVIEW] = WorkflowStageType.REVIEW

    def get_tasks(self) -> Iterable[ReviewTask]:
        for task in self.workflow_client.get_tasks(self.uuid, type_=ReviewTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self.workflow_client
            yield task


class ConsensusReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_REVIEW] = WorkflowStageType.CONSENSUS_REVIEW

    def get_tasks(self) -> Iterable[ConsensusReviewTask]:
        for task in self.workflow_client.get_tasks(self.uuid, type_=ConsensusReviewTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self.workflow_client
            yield task


class FinalStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.DONE] = WorkflowStageType.DONE

    def get_tasks(self) -> Iterable[FinalStageTask]:
        yield from self.workflow_client.get_tasks(self.uuid, type_=FinalStageTask)


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

        self.stages = [_construct_stage(workflow_client, stage) for stage in workflow_orm.stages]

    def get_stage(self, *, name: str | None = None, uuid: UUID | None = None) -> WorkflowStage:
        for stage in self.stages:
            if (uuid is not None and stage.uuid == uuid) or (name is not None and stage.title == name):
                return stage

        raise ValueError(f"No matching stage found: '{uuid or name}'")
