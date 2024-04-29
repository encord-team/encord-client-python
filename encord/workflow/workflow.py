from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Literal
from uuid import UUID

from typing_extensions import Annotated

from encord.orm.base_dto import Field
from encord.orm.workflow import Workflow as WorkflowORM
from encord.orm.workflow import WorkflowNode, WorkflowStageType


class Task:
    task_uuid: UUID


@dataclass(frozen=True)
class WorkflowStageBase:
    # stage_type: WorkflowStageType
    uuid: UUID
    title: str

    def __repr__(self):
        return f"{self.__class__.__name__}(stage_type={self.stage_type}, uuid='{self.uuid}', title='{self.title}')"


class AnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.ANNOTATION] = WorkflowStageType.ANNOTATION


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


def _construct_stage(node: WorkflowNode) -> WorkflowStage:
    match node.node_type:
        case WorkflowStageType.ANNOTATION:
            return AnnotationStage(uuid=node.uuid, title=node.title)
        case WorkflowStageType.REVIEW:
            return ReviewStage(uuid=node.uuid, title=node.title)
        case WorkflowStageType.CONSENSUS_ANNOTATION:
            return ConsensusAnnotationStage(uuid=node.uuid, title=node.title)
        case WorkflowStageType.CONSENSUS_REVIEW:
            return ConsensusReviewStage(uuid=node.uuid, title=node.title)
        case WorkflowStageType.DONE:
            return CompleteStage(uuid=node.uuid, title=node.title)
        case _:
            raise AssertionError(f"Unknown stage type: {node.node_type}")


class Workflow:
    stages: list[WorkflowStage] = []

    def __init__(self, workflow_orm: WorkflowORM):
        self.stages = [_construct_stage(x) for x in workflow_orm.stages]

    def get_stage(self, *, name: str | None = None, uuid: UUID | None = None) -> WorkflowStage:
        for stage in self.stages:
            if (uuid is not None and stage.uuid == uuid) or (name is not None and stage.title == name):
                return stage

        raise ValueError(f"No matching stage found: '{uuid or name}'")
