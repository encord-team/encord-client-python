"""
---
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
from typing import List, Literal, Optional, Union
from collections.abc import Iterable
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.http.bundle import Bundle
from encord.orm.base_dto import BaseDTO
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowAction, WorkflowStageBase, WorkflowTask


class ConsensusReviewTaskStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    RELEASED = "RELEASED"
    REOPENED = "REOPENED"


class _ReviewTasksQueryParams(TasksQueryParams):
    user_emails: list[str] | None = None
    data_hashes: list[UUID] | None = None
    dataset_hashes: list[UUID] | None = None
    data_title_contains: str | None = None
    statuses: list[ConsensusReviewTaskStatus] | None = None


class ConsensusReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_REVIEW] = WorkflowStageType.CONSENSUS_REVIEW

    """
    The Review stage for Consensus Workflows.
    """

    def get_tasks(
        self,
        *,
        assignee: list[str] | str | None = None,
        data_hash: list[UUID] | UUID | list[str] | str | None = None,
        dataset_hash: list[UUID] | UUID | list[str] | str | None = None,
        data_title: str | None = None,
        status: ConsensusReviewTaskStatus | list[ConsensusReviewTaskStatus] | None = None,
    ) -> Iterable[ConsensusReviewTask]:
        """
        Retrieves tasks for the ConsensusReviewStage.

        **Parameters**

        - `assignee` (Union[List[str], str, None]): A list of user emails or a single user email to filter tasks by assignee.
        - `data_hash` (Union[List[UUID], UUID, List[str], str, None]): A list of data unit UUIDs or a single data unit UUID to filter tasks by data hash.
        - `dataset_hash` (Union[List[UUID], UUID, List[str], str, None]): A list of dataset UUIDs or a single dataset UUID to filter tasks by dataset hash.
        - `data_title` (Optional[str]): A string to filter tasks by data title.
        - `status` (Union[ConsensusReviewTaskStatus, List[ConsensusReviewTaskStatus], None]): A list of task statuses or a single task status to filter tasks by their status.

        **Returns**

        An iterable of `ConsensusReviewTask` instances with the following information:
        - `uuid`: Unique identifier for the task.
        - `created_at`: Time and date the task was created.
        - `updated_at`: Time and date the task was last edited.
        - `assignee`: The user currently assigned to the task. The value is None if no one is assigned to the task.
        - `data_hash`: Unique identifier for the data unit.
        - `data_title`: Name/title of the data unit.
        - `options`: List of ConsensusReviewOptions. ConsensusReviewOptions are the labels available for each subtask, including information such as annotator, label_branch_name, and label_hash.
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
            yield task


class _ActionApprove(WorkflowAction):
    action: Literal["APPROVE"] = "APPROVE"
    assignee: str | None = None
    retain_assignee: bool = False


class _ActionReject(WorkflowAction):
    action: Literal["REJECT"] = "REJECT"
    assignee: str | None = None
    retain_assignee: bool = False


class _ActionAssign(WorkflowAction):
    action: Literal["ASSIGN"] = "ASSIGN"
    assignee: str


class _ActionRelease(WorkflowAction):
    action: Literal["RELEASE"] = "RELEASE"


class ConsensusReviewOption(BaseDTO):
    annotator: str
    label_branch_name: str
    label_hash: UUID | None


class ConsensusReviewTask(WorkflowTask):
    status: ConsensusReviewTaskStatus
    data_hash: UUID
    data_title: str
    assignee: str | None
    options: list[ConsensusReviewOption]

    """
    Represents tasks in the Review stage of a Consensus Project.

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
    """

    def approve(
        self,
        *,
        assignee: str | None = None,
        retain_assignee: bool = False,
        bundle: Bundle | None = None,
    ) -> None:
        """
        Approve the current task.

        **Parameters**

        - `assignee` (Optional[str]): User email to be assigned to the review task whilst approving the task.
        - `retain_assignee` (bool): Retains the current assignee whilst approving the task. This is ignored if `assignee` is provided. An error will occur if the task does not already have an assignee and `retain_assignee` is True.
        - `bundle` (Optional[Bundle]): Optional bundle of actions to execute with the approval.

        **Returns**

        None
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
        assignee: str | None = None,
        retain_assignee: bool = False,
        bundle: Bundle | None = None,
    ) -> None:
        """
        Reject the current task.

        **Parameters**

        - `assignee` (Optional[str]): User email to be assigned to the review task whilst rejecting the task.
        - `retain_assignee` (bool): Retains the current assignee whilst rejecting the task. This is ignored if `assignee` is provided. An error will occur if the task does not already have an assignee and `retain_assignee` is True.
        - `bundle` (Optional[Bundle]): Optional bundle of actions to execute with the rejection.

        **Returns**

        None
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(
            stage_uuid,
            _ActionReject(task_uuid=self.uuid, assignee=assignee, retain_assignee=retain_assignee),
            bundle=bundle,
        )

    def assign(self, assignee: str, *, bundle: Bundle | None = None) -> None:
        """
        Assign the current task to a user.

        **Parameters**

        - `assignee` (str): The user to assign the task to.
        - `bundle` (Optional[Bundle]): Optional bundle of actions to execute with the assignment.

        **Returns**

        None
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionAssign(task_uuid=self.uuid, assignee=assignee), bundle=bundle)

    def release(self, *, bundle: Bundle | None = None) -> None:
        """
        Release the current task from the current user.

        **Parameters**

        - `bundle` (Optional[Bundle]): Optional bundle of actions to execute with the release.

        **Returns**

        None
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionRelease(task_uuid=self.uuid), bundle=bundle)
