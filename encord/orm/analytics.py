from datetime import datetime
from enum import Enum, auto
from typing import List, Literal, Optional
from uuid import UUID

from encord.common.utils import snake_to_camel
from encord.orm.base_dto import BaseDTO
from encord.orm.workflow import BaseWorkflowNode, WorkflowNode, WorkflowStageType
from encord.utilities.project_user import ProjectUserRole


class CamelStrEnum(str, Enum):
    # noinspection PyMethodParameters
    def _generate_next_value_(name, start, count, last_values) -> str:  # type: ignore
        return snake_to_camel(name)


class CollaboratorTimersGroupBy(CamelStrEnum):
    """Grouping mode for collaborator time tracking analytics.

    **Values**:

    - **DATA_UNIT:** Group time spent per individual data unit.
    - **PROJECT:** Group time spent at the project level.
    """

    DATA_UNIT = auto()
    PROJECT = auto()


class CollaboratorTimerParams(BaseDTO):
    """Parameters for fetching collaborator timer analytics.

    Args:
        project_hash: Identifier of the project to query.
        after: Start of the time window (inclusive).
        before: Optional end of the time window (exclusive). If omitted, the server will typically use the current time.
        group_by: How to group results, for example by data unit or by project.
        page_size: Maximum number of records to return in a single page.
        page_token: Pagination token returned from a previous response, used to fetch the next page of results.
    """

    project_hash: str
    after: datetime
    before: Optional[datetime] = None
    group_by: CollaboratorTimersGroupBy = CollaboratorTimersGroupBy.DATA_UNIT
    page_size: int = 100
    page_token: Optional[str] = None


class CollaboratorTimer(BaseDTO):
    """Time spent by a single collaborator within the requested window.

    Args:
        user_email: Email address of the collaborator.
        user_role: Role of the user in the project (for example, annotator or reviewer).
        data_title: Optional title of the data item this timer row refers to. May be ``None`` when grouped at the project level.
        time_seconds: Total time spent (in seconds) matching the query filters.
    """

    user_email: str
    user_role: ProjectUserRole
    data_title: Optional[str] = None
    time_seconds: float


class TimeSpentParams(BaseDTO):
    """Filter parameters for fetching aggregated time spent analytics.

    Args:
        project_uuid: Unique identifier of the project to query.
        after: Start of the time window (inclusive).
        before: Optional end of the time window (exclusive). If omitted, uses current time.
        workflow_stage_uuids: Optional subset of workflow stages to include.
        user_emails: Optional list of user emails to filter by.
        dataset_uuids: Optional subset of datasets to include.
        data_uuids: Optional subset of data items to include.
        data_title: Optional fuzzy match string on data title.
        page_token: Pagination token from a previous response.
    """

    project_uuid: str
    after: datetime
    before: Optional[datetime] = None
    workflow_stage_uuids: Optional[List[UUID]] = None
    user_emails: Optional[List[str]] = None
    dataset_uuids: Optional[List[UUID]] = None
    data_uuids: Optional[List[UUID]] = None
    data_title: Optional[str] = None
    page_token: Optional[str] = None


class TimeSpent(BaseDTO):
    """Aggregated time spent for a user or stage within a time bucket.

    Args:
        period_start_time: Beginning of the aggregation period.
        period_end_time: End of the aggregation period.
        time_spent_seconds: Total time spent (in seconds) in this period.
        user_email: Email of the user this row refers to.
        project_user_role: Role of the user in the project (annotator, reviewer, etc.).
        data_uuid: Unique identifier of the data item.
        data_title: Human-readable title of the data item.
        dataset_uuid: Unique identifier of the dataset.
        dataset_title: Human-readable dataset title.
        workflow_task_uuid: Optional workflow task identifier.
        workflow_stage: Optional workflow stage object associated with this row.
    """

    period_start_time: datetime
    period_end_time: datetime
    time_spent_seconds: int
    user_email: str
    project_user_role: ProjectUserRole
    data_uuid: UUID
    data_title: str
    dataset_uuid: UUID
    dataset_title: str
    workflow_task_uuid: Optional[UUID] = None
    workflow_stage: Optional[BaseWorkflowNode] = None


class TaskActionType(CamelStrEnum):
    """Task action event types from workflow_task_events_v2 table."""

    ASSIGN = auto()
    APPROVE = auto()
    SUBMIT = auto()
    MOVE = auto()
    REJECT = auto()
    RELEASE = auto()
    SKIP = auto()


class TaskAction(BaseDTO):
    """Task action event returned by the task actions endpoint.

    Args:
        timestamp: Time when the action occurred.
        action_type: Type of action (e.g., ASSIGN, SUBMIT, APPROVE).
        project_uuid: UUID of the project.
        workflow_stage_uuid: UUID of the workflow stage.
        task_uuid: UUID of the task.
        data_unit_uuid: UUID of the data unit.
        actor_email: Email address of the user who performed the action.
    """

    timestamp: datetime
    action_type: TaskActionType
    project_uuid: UUID
    workflow_stage_uuid: UUID
    task_uuid: UUID
    data_unit_uuid: UUID
    actor_email: str


class TaskActionParams(BaseDTO):
    """Parameters for get_task_actions API call.

    Args:
        project_uuid: UUID of the project to query.
        after: Start of the time window (inclusive).
        before: End of the time window (exclusive).
        actor_email: Optional list of user email addresses to filter by.
        action_type: Optional list of action types to filter by.
        workflow_stage_uuid: Optional list of workflow stage UUIDs to filter by.
        data_unit_uuid: Optional list of data unit UUIDs to filter by.
    """

    project_uuid: UUID
    after: datetime
    before: datetime
    actor_email: Optional[List[str]] = None
    action_type: Optional[List[TaskActionType]] = None
    workflow_stage_uuid: Optional[List[UUID]] = None
    data_unit_uuid: Optional[List[UUID]] = None
    page_token: Optional[str] = None
