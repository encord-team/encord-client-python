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
from typing import Iterable, List, Literal, Optional, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.http.bundle import Bundle
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowAction, WorkflowStageBase, WorkflowTask


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

    ❗️ CRITICAL INFORMATION: To move (approve or reject) tasks in a REVIEW stage, you MUST assign yourself as the user assigned to the task.
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
        params = _ReviewTasksQueryParams(
            user_emails=ensure_list(assignee),
            data_hashes=ensure_uuid_list(data_hash),
            dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_contains=data_title,
            statuses=ensure_list(status),
        )

        """
        **Parameters**

        - assignee: User assigned to a task.
        - data_hash: Unique ID for the data unit.
        - dataset_hash: Unique ID for the dataset that the data unit belongs to.
        - data_title: Name of the data unit.

        **Returns**

        Returns a list of Review tasks (see `ReviewTask` class) in the stage with the following information:
:

        - uuid: Unique identifier for the task.
        - created_at: Time and date the task was created.
        - updated_at: Time and date the task was last edited.
        - assignee: The user currently assigned to the task. The value is None if no one is assigned to the task.
        - data_hash: Unique identifier for the data unit.
        - data_title: Name/title of the data unit.
        """
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

    **Params**

    - assignee: Optional[str]
    - data_hash: UUID
    - data_title: str

    Allowed actions:

    - approve: Approves a task.
    - reject: Rejects a task.
    - assign: Assigns a task to a user.
    - release: Releases a task from the current user.
    """

    def approve(self, *, bundle: Optional[Bundle] = None) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionApprove(task_uuid=self.uuid), bundle=bundle)

    def reject(self, *, bundle: Optional[Bundle] = None) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionReject(task_uuid=self.uuid), bundle=bundle)

    def assign(self, assignee: str, *, bundle: Optional[Bundle] = None) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionAssign(task_uuid=self.uuid, assignee=assignee), bundle=bundle)

    def release(self, *, bundle: Optional[Bundle] = None) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionRelease(task_uuid=self.uuid), bundle=bundle)
