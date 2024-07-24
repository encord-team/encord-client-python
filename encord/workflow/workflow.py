"""
---
title: "Workflow"
slug: "sdk-ref-workflows"
hidden: false
metadata:
  title: "Workflows"
  description: "Encord SDK Workflow class."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from typing import List, Optional, Type, TypeVar, Union
from uuid import UUID

from typing_extensions import Annotated

from encord.http.v2.api_client import ApiClient
from encord.objects.utils import checked_cast
from encord.orm.base_dto import Field
from encord.orm.workflow import Workflow as WorkflowDTO
from encord.orm.workflow import WorkflowNode, WorkflowStageType
from encord.workflow.common import WorkflowClient
from encord.workflow.stages.agent import AgentStage
from encord.workflow.stages.annotation import AnnotationStage
from encord.workflow.stages.consensus_annotation import ConsensusAnnotationStage
from encord.workflow.stages.consensus_review import ConsensusReviewStage
from encord.workflow.stages.final import FinalStage
from encord.workflow.stages.review import ReviewStage

WorkflowStage = Annotated[
    Union[AnnotationStage, ReviewStage, ConsensusAnnotationStage, ConsensusReviewStage, FinalStage, AgentStage],
    Field(discriminator="stage_type"),
]


def _construct_stage(workflow_client: WorkflowClient, node: WorkflowNode) -> WorkflowStage:
    if node.stage_type == WorkflowStageType.ANNOTATION:
        return AnnotationStage(uuid=node.uuid, title=node.title, _workflow_client=workflow_client)
    elif node.stage_type == WorkflowStageType.REVIEW:
        return ReviewStage(uuid=node.uuid, title=node.title, _workflow_client=workflow_client)
    elif node.stage_type == WorkflowStageType.CONSENSUS_ANNOTATION:
        return ConsensusAnnotationStage(uuid=node.uuid, title=node.title, _workflow_client=workflow_client)
    elif node.stage_type == WorkflowStageType.CONSENSUS_REVIEW:
        return ConsensusReviewStage(uuid=node.uuid, title=node.title, _workflow_client=workflow_client)
    elif node.stage_type == WorkflowStageType.DONE:
        return FinalStage(uuid=node.uuid, title=node.title, _workflow_client=workflow_client)
    elif node.stage_type == WorkflowStageType.AGENT:
        return AgentStage(uuid=node.uuid, title=node.title, _workflow_client=workflow_client)
    else:
        raise AssertionError(f"Unknown stage type: {node.stage_type}")


WorkflowStageT = TypeVar(
    "WorkflowStageT",
    AnnotationStage,
    ReviewStage,
    ConsensusAnnotationStage,
    ConsensusReviewStage,
    FinalStage,
    AgentStage,
)


def _ensure_uuid(v: str | UUID) -> UUID:
    if isinstance(v, UUID):
        return v
    else:
        return UUID(v)


class Workflow:
    stages: List[WorkflowStage] = []

    """
    Workflow class in Projects.
    """

    def __init__(self, api_client: ApiClient, project_hash: UUID, workflow_orm: WorkflowDTO):
        workflow_client = WorkflowClient(api_client, project_hash)

        self.stages = [_construct_stage(workflow_client, stage) for stage in workflow_orm.stages]

    def get_stage(
        self,
        *,
        name: Optional[str] = None,
        uuid: Optional[UUID | str] = None,
        type_: Optional[Type[WorkflowStageT]] = None,
    ) -> WorkflowStageT:
        """
        **Params**

        - name: Name of the stage.
        - uuid: Unique identifier for the stage.
        - type_: The type of stage.

        **Returns**

        Returns a list of Workflow stages (`type_`) from non-Consensus and Consensus Projects.
        """
        for stage in self.stages:
            if (uuid is not None and stage.uuid == _ensure_uuid(uuid)) or (name is not None and stage.title == name):
                if type_ is not None and not isinstance(stage, type_):
                    raise AssertionError(
                        f"Expected '{type_.__name__}' but got '{type(stage).__name__}' for the requested workflow stage '{uuid or name}'"
                    )
                return checked_cast(stage, type_)

        raise ValueError(f"No matching stage found: '{uuid or name}'")
