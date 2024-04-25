from enum import Enum
from typing import List
from uuid import UUID

from encord.orm.base_dto import BaseDTO


class WorkflowAction(str, Enum):
    REOPEN = "reopen"
    COMPLETE = "complete"


class LabelWorkflowGraphNode:
    pass


class LabelWorkflowGraphNodePayload(BaseDTO):
    action: str


class WorkflowNode(BaseDTO):
    uuid: UUID
    node_type: str
    title: str


class Workflow(BaseDTO):
    stages: List[WorkflowNode]
