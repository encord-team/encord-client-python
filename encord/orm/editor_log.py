from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, Annotated
from uuid import UUID

from pydantic import EmailStr, Field, RootModel

from encord.orm.base_dto import BaseDTO

# The below code should be a duplication of the Editor Log models in file : /fastapi_server/routers/models/model_editor_logs.py
# We are duplicating the models here to avoid exposing any internal enums or models in the public API

class WorkflowNodeType(StrEnum):
    START = "START"
    ANNOTATION = "ANNOTATION"
    REVIEW = "REVIEW"
    USER_ROUTER = "USER_ROUTER"
    PERCENTAGE_ROUTER = "PERCENTAGE_ROUTER"
    CONSENSUS_ANNOTATION = "CONSENSUS_ANNOTATION"
    CONSENSUS_REVIEW = "CONSENSUS_REVIEW"
    DONE = "DONE"
    AGENT = "AGENT"

class EditorLogsActionCategory(StrEnum):
    OBJECT = "object"
    CLASSIFICATION = "classification"
    TASK = "task"
    AGENT = "agent"
    EDITOR = "editor"

# class EditorLogMetadataPublic(BaseDTO):
#     actor_user_id: str
#     actor_organisation_id: int
#     actor_user_email: str
#     project_id: UUID
#     project_organisation_id: int
#     project_user_role: str
#     project_organisation_user_role: str
#     data_unit_title: str
#     data_unit_data_type: str
#     data_unit_dataset_id: UUID
#     data_unit_dataset_title: str
#     ontology_id: UUID
#     label_id: str
#     workflow_stage_type: WorkflowNodeType | Literal[""]
#     workflow_stage_title: str
#
#
# class EditorLogCommonPublic(BaseDTO):
#     action: str
#     action_category: EditorLogsActionCategory
#     data_unit_id: UUID
#     workflow_stage_id: UUID
#     branch_name: str
#     workflow_task_id: UUID
#     timestamp: datetime
#     session_id: UUID
#     event_information: dict[str, Any]
#
#
# class LabelAttributesPublic(BaseDTO):
#     label_name: str
#     feature_id: str
#     label_ranges: list[tuple[int, int]]
#
#
# class ObjectAttributesPublic(LabelAttributesPublic, BaseDTO):
#     object_shape: str
#     object_current_frame: int | None = None
#     object_hash: str
#     object_id: int | None = None
#
#
# class ClassificationAttributesPublic(LabelAttributesPublic, BaseDTO):
#     classification_hash: str
#
#
# class EditorLogGeneralPublic(EditorLogCommonPublic, EditorLogMetadataPublic):
#     pass
#
#
# class EditorLogGeneralActionPublic(EditorLogGeneralPublic):
#     action_category: Literal[
#         EditorLogsActionCategory.EDITOR,
#         EditorLogsActionCategory.TASK,
#         EditorLogsActionCategory.AGENT,
#     ]
#
#
# class EditorLogClassificationPublic(EditorLogGeneralPublic, ClassificationAttributesPublic):
#     action_category: Literal[EditorLogsActionCategory.CLASSIFICATION]
#
#
# class EditorLogObjectPublic(EditorLogGeneralPublic, ObjectAttributesPublic):
#     action_category: Literal[EditorLogsActionCategory.OBJECT]
#
#
# # Add ID via subclassingExpand commentComment on line R164Code has comments. Press enter to view.
# class EditorLogClassificationReadPublic(EditorLogClassificationPublic):
#     id: UUID
#
#
# class EditorLogObjectReadPublic(EditorLogObjectPublic):
#     id: UUID
#
#
# class EditorLogGeneralActionReadPublic(EditorLogGeneralActionPublic):
#     id: UUID
#
#
# EditorLogReadPublic = Annotated[
#     EditorLogClassificationReadPublic | EditorLogObjectReadPublic | EditorLogGeneralActionReadPublic,
#     Field(discriminator="action_category"),
# ]
#
#
# class EditorLogRootModelPublic(RootModel):
#     root: EditorLogReadPublic

#
class EditorLog(BaseDTO):
    id: UUID
    # common fields
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
    workflow_stage_type: WorkflowNodeType | Literal[""]
    workflow_stage_title: str
    event_information: dict[str, Any]

    # Label fields
    label_name: str | None = None
    feature_id: str | None = None
    label_ranges: list[tuple[int, int]] | None = None

    # Classification field
    classification_hash: str | None = None

    # Object fields
    object_shape: str | None = None
    object_current_frame: int | None = None
    object_hash: str | None = None
    object_id: int | None = None


class EditorLogsResponsePublic(BaseDTO):
    logs: list[EditorLog]
    next_page_token: str | None = None


class EditorLogParams(BaseDTO):
    start_time: datetime
    end_time: datetime
    limit: int
    page_token: str | None = None
    action: str | None = None
    actor_user_email: EmailStr | None = None
    workflow_stage_id: UUID | None = None
    data_unit_id: UUID | None = None
