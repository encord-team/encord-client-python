from collections import OrderedDict
from enum import Enum

from encord.orm import base_orm


class WorkflowAction(Enum):
    REOPEN = "reopen"
    COMPLETE = "complete"


class LabelWorkflowGraphNode:
    pass


class LabelWorkflowGraphNodePayload(base_orm.BaseORM):
    DB_FIELDS = OrderedDict([("action", str)])
