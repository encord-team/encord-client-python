from enum import Enum
from typing import Any, List, Union
from uuid import UUID

from typing_extensions import Annotated

from encord.orm.base_dto import BaseDTO, dto_validator


class WorkflowAction(str, Enum):
    """Actions that can be applied to a workflow stage for a task.

    **Values**:

    **REOPEN:** Reopen a task at a given stage.
    **COMPLETE:** Mark a task as completed at a given stage.
    """

    REOPEN = "reopen"
    COMPLETE = "complete"


class WorkflowStageType(str, Enum):
    """Type of a workflow stage in a project workflow.

    **Values**:

    **ANNOTATION:** Annotation stage where labelers create or edit labels.
    **REVIEW:** Review stage where labels are reviewed and approved/rejected.
    **USER_ROUTER:** Router stage that routes tasks based on user assignment rules.
    **PERCENTAGE_ROUTER:** Router stage that routes tasks based on percentage splits.
    **CONSENSUS_ANNOTATION:** Annotation stage with consensus logic applied across annotators.
    **CONSENSUS_REVIEW:** Review stage with consensus logic applied across reviewers.
    **DONE:** Terminal stage indicating that workflow processing is complete.
    **AGENT:** Agent stage where tasks are handled by an automated agent.
    """

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
    """Payload describing an action to perform on a label workflow node.

    Args:
        action: Workflow action to apply to the node (for example, reopen or complete).
    """

    action: WorkflowAction


class BaseWorkflowNode(BaseDTO):
    """Base class for workflow nodes in a project workflow graph.

    Args:
        stage_type: Type of the workflow stage (annotation, review, router, etc.).
        uuid: UUID of the workflow stage.
        title: Human-readable title of the stage.
    """

    stage_type: WorkflowStageType
    uuid: UUID
    title: str


class WorkflowNode(BaseWorkflowNode):
    """
    Standard workflow node.

    Represents all workflow stages except agent stages. Agent stages are
    represented by :class:`WorkflowAgentNode` instead and are validated
    separately.
    """

    @dto_validator(mode="before")
    def check_stage_type_not_agent(cls, v: Any) -> Any:
        # Handle creation of Object from dictionary or from cls() call
        stage_type = v.stage_type if isinstance(v, BaseWorkflowNode) else (v.get("stageType") or v.get("stage_type"))
        if stage_type == WorkflowStageType.AGENT:
            raise ValueError("stage_type cannot be AGENT for WorkflowNode")
        return v


class AgentNodePathway(BaseDTO):
    """Outgoing pathway from an agent workflow node.

    Args:
        uuid: UUID of the pathway itself.
        title:  Human-readable title or label for the pathway.
        destination_uuid: UUID of the destination workflow stage that this pathway leads to.
    """

    uuid: UUID
    title: str
    destination_uuid: UUID


class WorkflowAgentNode(BaseWorkflowNode):
    """Workflow node representing an agent stage.

    Agent stages route tasks automatically based on agent logic and can
    have multiple outgoing pathways defined by
    :class:`AgentNodePathway` objects.
    """

    @dto_validator(mode="before")
    def check_stage_type_agent(cls, v: Any) -> Any:
        # Handle creation of Object from dictionary or from cls() call
        stage_type = v.stage_type if isinstance(v, BaseWorkflowNode) else (v.get("stageType") or v.get("stage_type"))
        if stage_type != WorkflowStageType.AGENT:
            raise ValueError("stage_type must be AGENT for WorkflowNode")
        return v

    pathways: List[AgentNodePathway]


class WorkflowDTO(BaseDTO):
    """Full workflow definition for a project.

    Args:
        stages: List of workflow stages in the project workflow graph.
            This can include both standard workflow nodes and agent nodes.
    """

    stages: List[Union[WorkflowAgentNode, WorkflowNode]]
