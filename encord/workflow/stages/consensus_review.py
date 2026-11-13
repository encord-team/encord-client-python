"""---
title: "Consensus Review Stage"
slug: "sdk-ref-stage-consen-review"
hidden: false
metadata:
  title: "Consensus Review Stage"
  description: "Encord SDK Consensus Review Stage."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, List, Literal, Optional, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.http.bundle import Bundle
from encord.issues.issue_client import TaskIssues
from encord.orm.base_dto import BaseDTO
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowAction, WorkflowStageBase, WorkflowTask


class ConsensusReviewTaskStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    RELEASED = "RELEASED"
    REOPENED = "REOPENED"
    SKIPPED = "SKIPPED"

    UNKNOWN = "_UNKNOWN_"
    """
    Returned when the Encord platform reports a task status that this SDK version
    does not recognize.
    """

    @classmethod
    def _missing_(cls, value: Any) -> "ConsensusReviewTaskStatus":
        """Return UNKNOWN for any unrecognized consensus review task status values."""
        return cls.UNKNOWN


class _ReviewTasksQueryParams(TasksQueryParams):
    user_emails: Optional[List[str]] = None
    data_hashes: Optional[List[UUID]] = None
    dataset_hashes: Optional[List[UUID]] = None
    data_title_contains: Optional[str] = None
    statuses: Optional[List[ConsensusReviewTaskStatus]] = None


class ConsensusReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_REVIEW] = WorkflowStageType.CONSENSUS_REVIEW

    """
    The Review stage for Consensus Workflows.
    """

    def get_tasks(
        self,
        *,
        assignee: Union[List[str], str, None] = None,
        data_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        dataset_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        data_title: Optional[str] = None,
        status: Union[ConsensusReviewTaskStatus, List[ConsensusReviewTaskStatus], None] = None,
    ) -> Iterable[ConsensusReviewTask]:
        """Returns the tasks in this Consensus Review stage that match the given filters.

        All filters are optional. If you pass several, only tasks that match all of them are returned.

        Args:
            assignee: Only return tasks assigned to this user, or to any of these users. Pass user emails.
            data_hash: Only return tasks for this data unit, or for any of these data units.
            dataset_hash: Only return tasks for data units in this dataset, or in any of these datasets.
            data_title: Only return tasks whose data unit title contains this text.
            status: Only return tasks with this status, or with any of these statuses.

        Returns:
            Iterable[ConsensusReviewTask]: The matching tasks. Tasks are fetched page by page as you iterate. Each
                task's `options` are the label branches of its annotators, with the annotator, branch name, and label
                hash.
        """
        params = _ReviewTasksQueryParams(
            user_emails=ensure_list(assignee),
            data_hashes=ensure_uuid_list(data_hash),
            dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_contains=data_title,
            statuses=ensure_list(status),
        )

        for task in self._workflow_client.get_tasks(self.uuid, params, type_=ConsensusReviewTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self._workflow_client
            task._task_issues = TaskIssues(
                api_client=self._workflow_client.api_client,
                project_uuid=self._workflow_client.project_hash,
                data_uuid=task.data_hash,
            )
            yield task


class _ActionApprove(WorkflowAction):
    action: Literal["APPROVE"] = "APPROVE"
    assignee: Optional[str] = None
    retain_assignee: bool = False


class _ActionReject(WorkflowAction):
    action: Literal["REJECT"] = "REJECT"
    assignee: Optional[str] = None
    retain_assignee: bool = False


class _ActionAssign(WorkflowAction):
    action: Literal["ASSIGN"] = "ASSIGN"
    assignee: str


class _ActionRelease(WorkflowAction):
    action: Literal["RELEASE"] = "RELEASE"


class ConsensusReviewOption(BaseDTO):
    annotator: str
    label_branch_name: str
    label_hash: Optional[UUID]


class ConsensusReviewTask(WorkflowTask):
    """Represents tasks in the Review stage of a Consensus Project.

    **Attributes**

    - `status` (ConsensusReviewTaskStatus): The status of the review task.
    - `data_hash` (UUID): Unique ID for the data unit.
    - `data_title` (str): Name of the data unit.
    - `assignee` (Optional[str]): The user assigned to the task.
    - `options` (List[ConsensusReviewOption]): Specify the labels for the task.

    **Allowed actions**

    - `approve`: Approves a task.
    - `reject`: Rejects a task.
    - `assign`: Assigns a task to a user.
    - `release`: Releases a task from the current user.
    - `move`: Moves the review task to another stage in the workflow.
    """

    status: ConsensusReviewTaskStatus
    data_hash: UUID
    data_title: str
    assignee: Optional[str]
    options: List[ConsensusReviewOption]

    def approve(
        self,
        *,
        assignee: Optional[str] = None,
        retain_assignee: bool = False,
        bundle: Optional[Bundle] = None,
    ) -> None:
        """Approves the task and moves it along the stage's approval pathway.

        Before you approve the task, save the labels you chose to the data unit's `main` label row.

        Args:
            assignee: The email of the user to assign the task to while approving it.
            retain_assignee: If `True`, keep the task's current assignee while approving it. Ignored if `assignee` is
                provided. Raises an error if the task has no assignee.
            bundle: If not provided, the action is performed immediately. If provided, the action is deferred and
                performed together with the other operations in the bundle.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(
            stage_uuid,
            _ActionApprove(task_uuid=self.uuid, assignee=assignee, retain_assignee=retain_assignee),
            bundle=bundle,
        )

    def reject(
        self,
        *,
        assignee: Optional[str] = None,
        retain_assignee: bool = False,
        bundle: Optional[Bundle] = None,
    ) -> None:
        """Rejects the task and moves it along the stage's rejection pathway.

        Args:
            assignee: The email of the user to assign the task to while rejecting it.
            retain_assignee: If `True`, keep the task's current assignee while rejecting it. Ignored if `assignee` is
                provided. Raises an error if the task has no assignee.
            bundle: If not provided, the action is performed immediately. If provided, the action is deferred and
                performed together with the other operations in the bundle.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(
            stage_uuid,
            _ActionReject(task_uuid=self.uuid, assignee=assignee, retain_assignee=retain_assignee),
            bundle=bundle,
        )

    def assign(self, assignee: str, *, bundle: Optional[Bundle] = None) -> None:
        """Assigns the task to a user.

        Args:
            assignee: The email of the user to assign the task to.
            bundle: If not provided, the action is performed immediately. If provided, the action is deferred and
                performed together with the other operations in the bundle.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(
            stage_uuid,
            _ActionAssign(task_uuid=self.uuid, assignee=assignee),
            bundle=bundle,
        )

    def release(self, *, bundle: Optional[Bundle] = None) -> None:
        """Releases the task from its current assignee, so that another user can pick it up.

        Args:
            bundle: If not provided, the action is performed immediately. If provided, the action is deferred and
                performed together with the other operations in the bundle.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(
            stage_uuid,
            _ActionRelease(task_uuid=self.uuid),
            bundle=bundle,
        )

    def move(self, *, destination_stage_uuid: UUID, bundle: Optional[Bundle] = None) -> None:
        """Moves the Consensus Review task directly to another stage in the Workflow.

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
        assert self._task_issues
        return self._task_issues
