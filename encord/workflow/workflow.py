from __future__ import annotations

from uuid import UUID

from typing_extensions import Annotated

from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO, BaseDTOInterface, Field
from encord.orm.workflow import Workflow as WorkflowORM
from encord.orm.workflow import WorkflowNode, WorkflowStageType
from encord.workflow.common import WorkflowClient, WorkflowStageBase, WorkflowTask
from encord.workflow.stages.annotation import AnnotationStage, AnnotationTask
from encord.workflow.stages.consensus_annotation import ConsensusAnnotationStage
from encord.workflow.stages.consensus_review import ConsensusReviewStage
from encord.workflow.stages.final import FinalStage
from encord.workflow.stages.review import ReviewStage

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
