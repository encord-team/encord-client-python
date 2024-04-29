from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Literal, Optional
from uuid import UUID

from pydantic import BaseModel
from typing_extensions import Annotated

from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO, Field
from encord.orm.workflow import Workflow as WorkflowORM
from encord.orm.workflow import WorkflowNode, WorkflowStageType


class TaskInfo(BaseDTO):
    uuid: UUID


@dataclass
class Task:
    uuid: UUID


@dataclass
class AnnotationTask(Task):
    pass


class TasksQueryParams(BaseDTO):
    page_token: Optional[str] = None


@dataclass
class WorkflowClient:
    api_client: ApiClient
    project_hash: UUID

    def get_tasks(self, stage_uuid: UUID) -> Iterable[TaskInfo]:
        return self.api_client.get_paged_iterator(
            path=f"/projects/{self.project_hash}/workflow-stages/{stage_uuid}/tasks",
            params=TasksQueryParams(),
            result_type=TaskInfo,
        )


@dataclass(frozen=True)
class WorkflowStageBase:
    workflow_client: WorkflowClient

    # stage_type: WorkflowStageType
    uuid: UUID
    title: str

    def __repr__(self):
        return f"{self.__class__.__name__}(stage_type={self.stage_type}, uuid='{self.uuid}', title='{self.title}')"


class AnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.ANNOTATION] = WorkflowStageType.ANNOTATION

    def get_tasks(self) -> Iterable[AnnotationTask]:
        for task_info in self.workflow_client.get_tasks(self.uuid):
            yield AnnotationTask(uuid=task_info.uuid)


class ReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.REVIEW] = WorkflowStageType.REVIEW


class ConsensusAnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_ANNOTATION] = WorkflowStageType.CONSENSUS_ANNOTATION


class ConsensusReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_REVIEW] = WorkflowStageType.CONSENSUS_REVIEW


class CompleteStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.DONE] = WorkflowStageType.DONE


WorkflowStage = Annotated[
    AnnotationStage | ReviewStage | ConsensusAnnotationStage | ConsensusReviewStage | CompleteStage,
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
            return CompleteStage(uuid=node.uuid, title=node.title, workflow_client=workflow_client)
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
