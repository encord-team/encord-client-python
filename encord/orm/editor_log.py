from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from typing_extensions import Union

from encord.common.enum import StringEnum
from encord.orm.base_dto import BaseDTO

# types coming from cord/apiserver/public_api_v2/routers/models/model_editor_logs.py


class ActionableWorkflowNodeType(StringEnum):
    ANNOTATION = "ANNOTATION"
    REVIEW = "REVIEW"
    CONSENSUS_ANNOTATION = "CONSENSUS_ANNOTATION"
    CONSENSUS_REVIEW = "CONSENSUS_REVIEW"
    DONE = "DONE"


class EditorLogsActionCategory(StringEnum):
    OBJECT = "object"
    CLASSIFICATION = "classification"
    TASK = "task"
    AGENT = "agent"
    EDITOR = "editor"


class EditorLogCommon(BaseDTO):
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
    workflow_stage_type: ActionableWorkflowNodeType | Literal[""]
    workflow_stage_title: str
    event_information: dict[str, Any]


class LabelAttributes(BaseDTO):
    label_name: str
    feature_id: str
    label_ranges: list[tuple[int, int]]


class ObjectAttributes(LabelAttributes, BaseDTO):
    object_shape: str
    object_current_frame: int | None = None
    object_hash: str
    object_id: int | None = None


class ClassificationAttributes(LabelAttributes, BaseDTO):
    classification_hash: str


class EditorLogGeneralAction(EditorLogCommon):
    action_category: Literal[
        EditorLogsActionCategory.EDITOR,
        EditorLogsActionCategory.TASK,
        EditorLogsActionCategory.AGENT,
    ]


class EditorLogClassification(EditorLogCommon, ClassificationAttributes):
    action_category: Literal[EditorLogsActionCategory.CLASSIFICATION]


class EditorLogObject(EditorLogCommon, ObjectAttributes):
    action_category: Literal[EditorLogsActionCategory.OBJECT]


EditorLog = Union[EditorLogGeneralAction, EditorLogObject, EditorLogClassification]


class EditorLogParams(BaseDTO):
    start_time: datetime
    end_time: datetime
    action: str | None = None
    actor_user_email: str | None = None
    workflow_stage_id: UUID | None = None
    data_unit_id: UUID | None = None
    page_token: str | None = None
