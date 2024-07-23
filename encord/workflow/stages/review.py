"""
---
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
from typing import Iterable, List, Literal, Optional, Tuple, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.http.bundle import Bundle
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


class _LabelReviewActionApprove(WorkflowReviewAction):
    action: Literal["APPROVE"] = "APPROVE"


class _LabelReviewActionReject(WorkflowReviewAction):
    action: Literal["REJECT"] = "REJECT"


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
        """
        Approves the review.

        **Parameters**

        - `bundle` (Optional[Bundle]): Optional bundle parameter.
        """
        workflow_client, stage_uuid, task_uuid = self._get_client_data()
        workflow_client.label_review_action(
            stage_uuid, task_uuid, _LabelReviewActionApprove(review_uuid=self.uuid), bundle=bundle
        )

    def reject(self, *, bundle: Optional[Bundle] = None):
        """
        Rejects the review.

        **Parameters**

        - `bundle` (Optional[Bundle]): Optional bundle parameter.
        """
        workflow_client, stage_uuid, task_uuid = self._get_client_data()
        workflow_client.label_review_action(
            stage_uuid, task_uuid, _LabelReviewActionReject(review_uuid=self.uuid), bundle=bundle
        )

    def reopen(self, *, bundle: Optional[Bundle] = None):
        """
        Reopens the review.

        **Parameters**

        - `bundle` (Optional[Bundle]): Optional bundle parameter.
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
        """
        Retrieves tasks for the ReviewStage.

        **Parameters**

        - `assignee` (Union[List[str], str, None]): User assigned to a task.
        - `data_hash` (Union[List[UUID], UUID, List[str], str, None]): Unique ID for the data unit.
        - `dataset_hash` (Union[List[UUID], UUID, List[str], str, None]): Unique ID for the dataset that the data unit belongs to.
        - `data_title` (Optional[str]): Name of the data unit.
        - `status` (Union[ReviewTaskStatus, List[ReviewTaskStatus], None]): Status of the task.

        **Returns**

        An iterable of `ReviewTask` instances with the following information:
        - `uuid`: Unique identifier for the task.
        - `created_at`: Time and date the task was created.
        - `updated_at`: Time and date the task was last edited.
        - `assignee`: The user currently assigned to the task. The value is None if no one is assigned to the task.
        - `data_hash`: Unique identifier for the data unit.
        - `data_title`: Name/title of the data unit.
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
            yield task


class _ActionApprove(WorkflowAction):
    action: Literal["APPROVE"] = "APPROVE"
    approve_label_reviews: bool = True


class _ActionReject(WorkflowAction):
    action: Literal["REJECT"] = "REJECT"
    reject_label_reviews: bool = True


class _ActionAssign(WorkflowAction):
    action: Literal["ASSIGN"] = "ASSIGN"
    assignee: str


class _ActionRelease(WorkflowAction):
    action: Literal["RELEASE"] = "RELEASE"


class ReviewTask(WorkflowTask):
    status: ReviewTaskStatus
    data_hash: UUID
    data_title: str
    assignee: Optional[str]

    """
    Tasks in non-Consensus Review stages.

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
    """

    def approve(self, *, bundle: Optional[Bundle] = None) -> None:
        """
        Approves the task.

        **Parameters**

        - `bundle` (Optional[Bundle]): Optional bundle parameter.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionApprove(task_uuid=self.uuid), bundle=bundle)

    def reject(self, *, bundle: Optional[Bundle] = None) -> None:
        """
        Rejects the task.

        **Parameters**

        - `bundle` (Optional[Bundle]): Optional bundle parameter.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionReject(task_uuid=self.uuid), bundle=bundle)

    def assign(self, assignee: str, *, bundle: Optional[Bundle] = None) -> None:
        """
        Assigns the task to a user.

        **Parameters**

        - `assignee` (str): The user to assign the task to.
        - `bundle` (Optional[Bundle]): Optional bundle parameter.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionAssign(task_uuid=self.uuid, assignee=assignee), bundle=bundle)

    def release(self, *, bundle: Optional[Bundle] = None) -> None:
        """
        Releases the task from the current user.

        **Parameters**

        - `bundle` (Optional[Bundle]): Optional bundle parameter.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionRelease(task_uuid=self.uuid), bundle=bundle)

    def get_label_reviews(
        self, status: Union[ReviewTaskStatus, List[ReviewTaskStatus], None] = None
    ) -> Iterable[LabelReview]:
        """
        Retrieves label reviews for the Review task.

        **Parameters**
        - `status` (Union[ReviewTaskStatus, List[ReviewTaskStatus], None]): Status of the task.

        **Returns**

        An iterable of `ReviewTask` instances with the following information:
        - `uuid`: Unique identifier for label review.
        - `status`: Current status of the label review.
        - `label_type`: Type of the label. Can be either Object or Classification.
        - `label_id`: Unique identifier of the label.
        """
        workflow_client, stage_uuid = self._get_client_data()
        for r in workflow_client.get_label_reviews(stage_uuid, self.uuid, type_=LabelReview):
            r._workflow_client = self._workflow_client
            r._stage_uuid = self._stage_uuid
            r._task_uuid = self.uuid
            yield r
