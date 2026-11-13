from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, List, Literal, Optional, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.http.bundle import Bundle
from encord.issues.issue_client import TaskIssues
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowAction, WorkflowStageBase, WorkflowTask


class AgentTaskStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    RELEASED = "RELEASED"
    SKIPPED = "SKIPPED"
    REOPENED = "REOPENED"
    COMPLETED = "COMPLETED"

    UNKNOWN = "_UNKNOWN_"
    """
    Returned when the Encord platform reports a task status that this SDK version
    does not recognize.
    """

    @classmethod
    def _missing_(cls, value: Any) -> "AgentTaskStatus":
        """Return UNKNOWN for any unrecognized agent task status values."""
        return cls.UNKNOWN


class _ActionPathway(WorkflowAction):
    action: Literal["PATHWAY_ACTION"] = "PATHWAY_ACTION"
    pathway_uuid: Optional[Union[str, UUID]] = None
    pathway_name: Optional[str] = None


class AgentTask(WorkflowTask):
    """Represents a task in an Agent stage.

    **Attributes**

    - `status` (AgentTaskStatus): The current status of the task.
    - `data_hash` (UUID): Unique ID for the data unit.
    - `data_title` (str): Name of the data unit.
    - `label_branch_name` (str): Name of the label branch.
    - `assignee` (Optional[str]): User assigned to the task.
    - `last_actioned_by` (Optional[str]): User who last acted on the task.

    **Allowed actions**

    - `proceed`: Advance the task along a specific pathway from the current stage.
    - `move`: Move the task directly to another stage in the workflow.
    """

    status: AgentTaskStatus
    data_hash: UUID
    data_title: str
    label_branch_name: str
    assignee: Optional[str]
    last_actioned_by: Optional[str]

    def proceed(
        self,
        pathway_name: Optional[str] = None,
        pathway_uuid: Optional[Union[UUID, str]] = None,
        *,
        bundle: Optional[Bundle] = None,
    ) -> None:
        """Moves the task along one of the Agent stage's pathways.

        Pass `pathway_name` or `pathway_uuid` to choose the pathway. The stage's pathways are listed in
        `AgentStage.pathways`.

        Args:
            pathway_name: The name of the pathway to follow.
            pathway_uuid: The UUID of the pathway to follow.
            bundle: If not provided, the action is performed immediately. If provided, the action is deferred and
                performed together with the other operations in the bundle.

        Raises:
            ValueError: If neither `pathway_name` nor `pathway_uuid` is provided.
        """
        if not pathway_name and not pathway_uuid:
            raise ValueError("Either `pathway_name` or `pathway_uuid` parameter must be provided.")

        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(
            stage_uuid,
            _ActionPathway(
                task_uuid=self.uuid,
                pathway_name=pathway_name,
                pathway_uuid=pathway_uuid,
            ),
            bundle=bundle,
        )

    def move(self, *, destination_stage_uuid: UUID, bundle: Optional[Bundle] = None) -> None:
        """Moves the Agent task directly to another stage in the Workflow.

        The task skips any stages in between. Webhooks don't fire for moved tasks, and labels are approved automatically
        when a task is moved to a Complete stage.

        Args:
            destination_stage_uuid: The UUID of the stage to move the task to.
            bundle: If not provided, the action is performed immediately. If provided, the action is deferred and
                performed together with the other operations in the bundle.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.move(
            origin_stage_uuid=stage_uuid,
            destination_stage_uuid=destination_stage_uuid,
            task_uuids=[self.uuid],
            bundle=bundle,
        )

    @property
    def issues(self) -> TaskIssues:
        """Returns the issue client for the task."""
        if self._task_issues is None:
            raise RuntimeError("Task issues are not initialized for this task.")
        return self._task_issues


class _AgentTasksQueryParams(TasksQueryParams):
    user_emails: Optional[List[str]] = None
    data_hashes: Optional[List[UUID]] = None
    dataset_hashes: Optional[List[UUID]] = None
    data_title_contains: Optional[str] = None
    statuses: Optional[List[AgentTaskStatus]] = None


@dataclass(frozen=True)
class AgentPathway:
    uuid: UUID
    name: str
    destination_uuid: UUID


@dataclass(frozen=True)
class AgentStage(WorkflowStageBase):
    pathways: List[AgentPathway]
    stage_type: Literal[WorkflowStageType.AGENT] = WorkflowStageType.AGENT

    """
    An Agent stage.
    """

    def get_tasks(
        self,
        *,
        assignee: Union[List[str], str, None] = None,
        data_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        dataset_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        data_title: Optional[str] = None,
        status: Optional[Union[AgentTaskStatus, List[AgentTaskStatus]]] = None,
    ) -> Iterable[AgentTask]:
        """Returns the tasks in this Agent stage that match the given filters.

        All filters are optional. If you pass several, only tasks that match all of them are returned.

        Args:
            assignee: Only return tasks assigned to this user, or to any of these users. Pass user emails.
            data_hash: Only return tasks for this data unit, or for any of these data units.
            dataset_hash: Only return tasks for data units in this dataset, or in any of these datasets.
            data_title: Only return tasks whose data unit title contains this text.
            status: Only return tasks with this status, or with any of these statuses.

        Returns:
            Iterable[AgentTask]: The matching tasks. Tasks are fetched page by page as you iterate.
        """
        params = _AgentTasksQueryParams(
            user_emails=ensure_list(assignee),
            data_hashes=ensure_uuid_list(data_hash),
            dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_contains=data_title,
            statuses=ensure_list(status),
        )

        for task in self._workflow_client.get_tasks(self.uuid, params, type_=AgentTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self._workflow_client
            task._task_issues = TaskIssues(
                api_client=self._workflow_client.api_client,
                project_uuid=self._workflow_client.project_hash,
                data_uuid=task.data_hash,
            )
            yield task
