from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional, Tuple
from uuid import UUID

from typing_extensions import Union

from encord.common.enum import StringEnum
from encord.orm.base_dto import BaseDTO

# types coming from cord/apiserver/public_api_v2/routers/models/model_editor_logs.py


class ActionableWorkflowNodeType(StringEnum):
    """Enumeration of workflow node types that can produce actionable editor logs."""

    ANNOTATION = "ANNOTATION"
    REVIEW = "REVIEW"
    CONSENSUS_ANNOTATION = "CONSENSUS_ANNOTATION"
    CONSENSUS_REVIEW = "CONSENSUS_REVIEW"
    DONE = "DONE"


class EditorLogsActionCategory(StringEnum):
    """High-level category describing the source or domain of an editor log action."""

    OBJECT = "object"
    CLASSIFICATION = "classification"
    TASK = "task"
    AGENT = "agent"
    EDITOR = "editor"


class EditorLogCommon(BaseDTO):
    """Base DTO shared by all editor log entries.

    Contains metadata describing *who* performed an action, *when* it occurred,
    *where* in the workflow it happened, and *what* project/data unit it relates to.
    """

    id: UUID
    action: str
    action_category: EditorLogsActionCategory
    data_unit_id: UUID
    workflow_stage_id: UUID
    branch_name: str
    workflow_task_id: UUID
    timestamp: datetime
    session_id: UUID
    actor_user_id: str
    actor_organisation_id: int
    actor_user_email: str
    project_id: UUID
    project_organisation_id: int
    project_user_role: str
    project_organisation_user_role: str
    data_unit_title: str
    data_unit_data_type: str
    data_unit_dataset_id: UUID
    data_unit_dataset_title: str
    ontology_id: UUID
    label_id: str
    workflow_stage_type: Union[ActionableWorkflowNodeType, Literal[""]]
    workflow_stage_title: str


class LabelAttributes(BaseDTO):
    """Attributes common to editor log entries that are associated with a label.

    This includes the label identity and the frame ranges over which the label applies.
    """

    label_name: str
    feature_id: str
    label_ranges: List[Tuple[int, int]]


class ObjectAttributes(LabelAttributes, BaseDTO):
    """Attributes specific to object-level editor actions.

    Extends label attributes with spatial and temporal object metadata.
    """

    object_shape: str
    object_current_frame: Optional[int] = None
    object_hash: str
    object_id: Optional[int] = None


class ClassificationAttributes(LabelAttributes, BaseDTO):
    """Attributes specific to classification-level editor actions."""

    classification_hash: str


class EditorLogGeneralAction(EditorLogCommon):
    """Editor log entry representing general actions not tied to objects or classifications.

    This includes editor UI actions, task-level events, and agent-driven actions.
    """

    action_category: Literal[
        EditorLogsActionCategory.EDITOR,
        EditorLogsActionCategory.TASK,
        EditorLogsActionCategory.AGENT,
    ]


class EditorLogClassification(EditorLogCommon, ClassificationAttributes):
    """Editor log entry representing actions performed on classification labels."""

    action_category: Literal[EditorLogsActionCategory.CLASSIFICATION]


class EditorLogObject(EditorLogCommon, ObjectAttributes):
    """Editor log entry representing actions performed on object labels."""

    action_category: Literal[EditorLogsActionCategory.OBJECT]


EditorLog = Union[
    EditorLogGeneralAction,
    EditorLogObject,
    EditorLogClassification,
]
"""Union type representing any possible editor log entry.
"""


class EditorLogParams(BaseDTO):
    """Parameters used to query or filter editor logs.

    Supports time-based filtering as well as optional constraints on user,
    workflow stage, and data unit.
    """

    start_time: datetime
    end_time: datetime
    action: Optional[str] = None
    actor_user_email: Optional[str] = None
    workflow_stage_id: Optional[UUID] = None
    data_unit_id: Optional[UUID] = None
    page_token: Optional[str] = None
