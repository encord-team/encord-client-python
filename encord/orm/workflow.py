from enum import Enum
from typing import Any, List, Union
from uuid import UUID

from typing_extensions import Annotated

from encord.orm.base_dto import BaseDTO, dto_validator


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
    action: WorkflowAction


class BaseWorkflowNode(BaseDTO):
    stage_type: WorkflowStageType
    uuid: UUID
    title: str


class WorkflowNode(BaseWorkflowNode):
    @dto_validator(mode="before")
    def check_stage_type_not_agent(cls, v: Any) -> Any:
        # Handle creation of Object from dictionary or from cls() call
        stage_type = v.stage_type if isinstance(v, BaseWorkflowNode) else (v.get("stageType") or v.get("stage_type"))
        if stage_type == WorkflowStageType.AGENT:
            raise ValueError("stage_type cannot be AGENT for WorkflowNode")
        return v


class AgentNodePathway(BaseDTO):
    uuid: UUID
    title: str
    destination_uuid: UUID


class WorkflowAgentNode(BaseWorkflowNode):
    @dto_validator(mode="before")
    def check_stage_type_agent(cls, v: Any) -> Any:
        # Handle creation of Object from dictionary or from cls() call
        stage_type = v.stage_type if isinstance(v, BaseWorkflowNode) else (v.get("stageType") or v.get("stage_type"))
        if stage_type != WorkflowStageType.AGENT:
            raise ValueError("stage_type must be AGENT for WorkflowNode")
        return v

    pathways: List[AgentNodePathway]


class WorkflowDTO(BaseDTO):
    stages: List[Union[WorkflowAgentNode, WorkflowNode]]
