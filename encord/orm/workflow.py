from enum import Enum
from typing import List, Union
from uuid import UUID

from typing_extensions import Annotated

from encord.orm.base_dto import BaseDTO, Discriminator, Field, Tag, dto_validator


class WorkflowAction(str, Enum):
    REOPEN = "reopen"
    COMPLETE = "complete"


class WorkflowStageType(str, Enum):
    ANNOTATION = "ANNOTATION"
    REVIEW = "REVIEW"
    USER_ROUTER = "USER_ROUTER"
    PERCENTAGE_ROUTER = "PERCENTAGE_ROUTER"
    CONSENSUS_ANNOTATION = "CONSENSUS_ANNOTATION"
    CONSENSUS_REVIEW = "CONSENSUS_REVIEW"
    DONE = "DONE"
    AGENT = "AGENT"


class LabelWorkflowGraphNode:
    """
    This class only required to indicate correct request type to basic querier,
    don't use this anywhere else.
    """

    pass


class LabelWorkflowGraphNodePayload(BaseDTO):
    action: str


class WorkflowNode(BaseDTO):
    stage_type: WorkflowStageType
    uuid: UUID
    title: str


class AgentNodePathway(BaseDTO):
    uuid: UUID
    title: str
    destination_uuid: UUID


class WorkflowAgentNode(WorkflowNode):
    stage_type: WorkflowStageType = WorkflowStageType.AGENT
    pathways: List[AgentNodePathway]


def _get_discriminator_value(model: dict) -> str:
    stage_type = model["stageType"]
    if stage_type == WorkflowStageType.AGENT:
        return "AGENT"
    return "GENERIC"


class Workflow(BaseDTO):
    stages: List[
        Annotated[
            Union[Annotated[WorkflowNode, Tag("GENERIC")], Annotated[WorkflowAgentNode, Tag("AGENT")]],
            Discriminator(_get_discriminator_value),
        ]
    ]
