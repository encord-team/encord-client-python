from __future__ import annotations

from typing import Optional, Type, TypeVar, Union, cast
from uuid import UUID

from typing_extensions import Annotated

from encord.http.v2.api_client import ApiClient
from encord.objects.utils import (
    check_type,
    checked_cast,
    does_type_match,
    short_uuid_str,
)
from encord.orm.base_dto import Field
from encord.orm.workflow import Workflow as WorkflowORM
from encord.orm.workflow import WorkflowNode, WorkflowStageType
from encord.workflow.common import WorkflowClient
from encord.workflow.stages.annotation import AnnotationStage
from encord.workflow.stages.consensus_annotation import ConsensusAnnotationStage
from encord.workflow.stages.consensus_review import ConsensusReviewStage
from encord.workflow.stages.final import FinalStage
from encord.workflow.stages.review import ReviewStage

WorkflowStage = Annotated[
    Union[AnnotationStage, ReviewStage, ConsensusAnnotationStage, ConsensusReviewStage, FinalStage],
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


WorkflowStageT = TypeVar(
    "WorkflowStageT", AnnotationStage, ReviewStage, ConsensusAnnotationStage, ConsensusReviewStage, FinalStage
)


class Workflow:
    stages: list[WorkflowStage] = []

    def __init__(self, api_client: ApiClient, project_hash: UUID, workflow_orm: WorkflowORM):
        workflow_client = WorkflowClient(api_client, project_hash)

        self.stages = [_construct_stage(workflow_client, stage) for stage in workflow_orm.stages]

    def get_stage(
        self, *, name: Optional[str] = None, uuid: Optional[UUID] = None, type_: Optional[Type[WorkflowStageT]] = None
    ) -> WorkflowStageT:
        for stage in self.stages:
            if (uuid is not None and stage.uuid == uuid) or (name is not None and stage.title == name):
                if type_ is not None and not isinstance(stage, type_):
                    raise AssertionError(
                        f"Expected '{type_.__name__}' but got '{type(stage).__name__}' for the requested workflow stage '{uuid or name}'"
                    )
                return checked_cast(stage, type_)

        raise ValueError(f"No matching stage found: '{uuid or name}'")
