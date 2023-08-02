from enum import Enum

from encord.orm.base_dto import BaseDTO


class WorkflowAction(str, Enum):
    REOPEN = "reopen"
    COMPLETE = "complete"


class LabelWorkflowGraphNode:
    pass


class LabelWorkflowGraphNodePayload(BaseDTO):
    action: str
