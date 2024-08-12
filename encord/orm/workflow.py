from enum import Enum
from typing import List
from uuid import UUID

from encord.orm.base_dto import BaseDTO


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
    pass


class LabelWorkflowGraphNodePayload(BaseDTO):
    action: str


class WorkflowNode(BaseDTO):
    uuid: UUID
    stage_type: WorkflowStageType
    title: str


class Workflow(BaseDTO):
    stages: List[WorkflowNode]
