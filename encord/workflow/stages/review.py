"""---
title: "Review Stage"
slug: "sdk-ref-stage-review"
hidden: false
metadata:
  title: "Review Stage"
  description: "Encord SDK Review Stage."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, List, Literal, Optional, Tuple, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.http.bundle import Bundle
from encord.issues.issue_client import TaskIssues
from encord.orm.base_dto import BaseDTO, Field, PrivateAttr
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import (
    TasksQueryParams,
    WorkflowAction,
    WorkflowClient,
    WorkflowReviewAction,
    WorkflowStageBase,
    WorkflowTask,
)


class LabelReviewStatus(str, Enum):
    NEW = "NEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"

    UNKNOWN = "_UNKNOWN_"
    """
    Returned when the Encord platform reports a label review status that this SDK version
    does not recognize.
    """

    @classmethod
    def _missing_(cls, value: Any) -> "LabelReviewStatus":
        """Return UNKNOWN for any unrecognized label review status values."""
        return cls.UNKNOWN


class _LabelReviewActionApprove(WorkflowReviewAction):
    action: Literal["APPROVE"] = "APPROVE"


class _LabelReviewActionReject(WorkflowReviewAction):
    action: Literal["REJECT"] = "REJECT"
    comment: Optional[str] = None
    comment_tags: Optional[List[str]] = None


class _LabelReviewActionReopen(WorkflowReviewAction):
    action: Literal["REOPEN"] = "REOPEN"


class LabelReview(BaseDTO):
    _workflow_client: Optional[WorkflowClient] = PrivateAttr(None)
    _stage_uuid: Optional[UUID] = PrivateAttr(None)
    _task_uuid: Optional[UUID] = PrivateAttr(None)

    uuid: UUID = Field(alias="reviewUuid")
    status: LabelReviewStatus

    label_type: str
    label_id: str

    def _get_client_data(self) -> Tuple[WorkflowClient, UUID, UUID]:
        assert self._workflow_client
        assert self._stage_uuid
        assert self._task_uuid
        return self._workflow_client, self._stage_uuid, self._task_uuid

    def approve(self, *, bundle: Optional[Bundle] = None):
        """Approves this label review.

        Args:
            bundle: If not provided, the action is performed immediately. If provided, the action is deferred and
                performed together with the other operations in the bundle.
        """
        workflow_client, stage_uuid, task_uuid = self._get_client_data()
        workflow_client.label_review_action(
            stage_uuid, task_uuid, _LabelReviewActionApprove(review_uuid=self.uuid), bundle=bundle
        )

    def reject(
        self,
        *,
        comment: Optional[str] = None,
        issue_tags: Optional[List[str]] = None,
        bundle: Optional[Bundle] = None,
    ):
        """Rejects this label review.

        Args:
            comment: An optional comment explaining the rejection.
            issue_tags: Optional issue tags to add to the rejection.
            bundle: If not provided, the action is performed immediately. If provided, the action is deferred and
                performed together with the other operations in the bundle.
        """
        workflow_client, stage_uuid, task_uuid = self._get_client_data()
        workflow_client.label_review_action(
            stage_uuid,
            task_uuid,
            _LabelReviewActionReject(review_uuid=self.uuid, comment=comment, comment_tags=issue_tags),
            bundle=bundle,
        )

    def reopen(self, *, bundle: Optional[Bundle] = None):
        """Reopens this label review, so that it can be approved or rejected again.

        Args:
            bundle: If not provided, the action is performed immediately. If provided, the action is deferred and
                performed together with the other operations in the bundle.
        """
        workflow_client, stage_uuid, task_uuid = self._get_client_data()
        workflow_client.label_review_action(
            stage_uuid, task_uuid, _LabelReviewActionReopen(review_uuid=self.uuid), bundle=bundle
        )


class ReviewTaskStatus(str, Enum):
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
    def _missing_(cls, value: Any) -> "ReviewTaskStatus":
        """Return UNKNOWN for any unrecognized review task status values."""
        return cls.UNKNOWN


class _ReviewTasksQueryParams(TasksQueryParams):
    user_emails: Optional[List[str]] = None
    data_hashes: Optional[List[UUID]] = None
    dataset_hashes: Optional[List[UUID]] = None
    data_title_contains: Optional[str] = None
    statuses: Optional[List[ReviewTaskStatus]] = None


class ReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.REVIEW] = WorkflowStageType.REVIEW

    """
    The Review stage for Workflows.

    This stage can appear in Consensus and non-Consensus Workflows.
    """

    def get_tasks(
        self,
        *,
        assignee: Union[List[str], str, None] = None,
        data_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        dataset_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        data_title: Optional[str] = None,
        status: Union[ReviewTaskStatus, List[ReviewTaskStatus], None] = None,
    ) -> Iterable[ReviewTask]:
        """Returns the tasks in this Review stage that match the given filters.

        All filters are optional. If you pass several, only tasks that match all of them are returned.

        Args:
            assignee: Only return tasks assigned to this user, or to any of these users. Pass user emails.
            data_hash: Only return tasks for this data unit, or for any of these data units.
            dataset_hash: Only return tasks for data units in this dataset, or in any of these datasets.
            data_title: Only return tasks whose data unit title contains this text.
            status: Only return tasks with this status, or with any of these statuses.

        Returns:
            Iterable[ReviewTask]: The matching tasks. Tasks are fetched page by page as you iterate.
        """
        params = _ReviewTasksQueryParams(
            user_emails=ensure_list(assignee),
            data_hashes=ensure_uuid_list(data_hash),
            dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_contains=data_title,
            statuses=ensure_list(status),
        )

        for task in self._workflow_client.get_tasks(self.uuid, params, type_=ReviewTask):
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
    approve_label_reviews: bool = True
    assignee: Optional[str] = None
    retain_assignee: bool = False


class _ActionReject(WorkflowAction):
    action: Literal["REJECT"] = "REJECT"
    reject_label_reviews: bool = True
    assignee: Optional[str] = None
    retain_assignee: bool = False


class _ActionAssign(WorkflowAction):
    action: Literal["ASSIGN"] = "ASSIGN"
    assignee: str


class _ActionRelease(WorkflowAction):
    action: Literal["RELEASE"] = "RELEASE"


class ReviewTask(WorkflowTask):
    """Represents tasks in non-Consensus Review stages.

    **Attributes**

    - `status` (ReviewTaskStatus): Status of the review task.
    - `data_hash` (UUID): Unique identifier for the data unit.
    - `data_title` (str): Name of the data unit.
    - `assignee` (Optional[str]): User assigned to the task.

    **Allowed actions**

    - `approve`: Approves a task.
    - `reject`: Rejects a task.
    - `assign`: Assigns a task to a user.
    - `release`: Releases a task from the current user.
    - `move`: Moves the review task to another stage in the workflow.
    """

    status: ReviewTaskStatus
    data_hash: UUID
    data_title: str
    assignee: Optional[str]

    def approve(
        self,
        *,
        assignee: Optional[str] = None,
        retain_assignee: bool = False,
        bundle: Optional[Bundle] = None,
    ) -> None:
        """Approves the task and moves it along the stage's approval pathway.

        Approving the task also approves all of its label reviews that haven't been approved or rejected yet.

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

        Rejecting the task also rejects all of its label reviews that haven't been approved or rejected yet.

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
        """Moves the task directly to another stage in the Workflow.

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

    def get_label_reviews(
        self, status: Union[ReviewTaskStatus, List[ReviewTaskStatus], None] = None
    ) -> Iterable[LabelReview]:
        """Returns the label reviews of this task: one for each object or classification being reviewed.

        Use the label reviews to approve, reject, or reopen individual labels.

        Args:
            status: Not currently applied. All of the task's label reviews are returned, whatever their status. Filter
                on each label review's `status` instead.

        Returns:
            Iterable[LabelReview]: The task's label reviews, each with its `uuid`, `status`, `label_type` (object or
                classification), and `label_id`.
        """
        workflow_client, stage_uuid = self._get_client_data()
        for r in workflow_client.get_label_reviews(stage_uuid, self.uuid, type_=LabelReview):
            r._workflow_client = self._workflow_client
            r._stage_uuid = self._stage_uuid
            r._task_uuid = self.uuid
            yield r

    @property
    def issues(self) -> TaskIssues:
        """Returns the issue client for the task."""
        assert self._task_issues
        return self._task_issues
