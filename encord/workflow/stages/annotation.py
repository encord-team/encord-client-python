"""
---
title: "Annotation Stage"
slug: "sdk-ref-stage-annotation"
hidden: false
metadata:
  title: "Annotation Stage"
  description: "Encord SDK Annotation Stage."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Iterable, List, Literal, Optional, TypeVar, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.http.bundle import Bundle
from encord.orm.base_dto import BaseDTO
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowAction, WorkflowStageBase, WorkflowTask


class AnnotationTaskStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    RELEASED = "RELEASED"
    SKIPPED = "SKIPPED"
    REOPENED = "REOPENED"
    COMPLETED = "COMPLETED"


class _AnnotationTasksQueryParams(TasksQueryParams):
    user_emails: Optional[List[str]] = None
    data_hashes: Optional[List[UUID]] = None
    dataset_hashes: Optional[List[UUID]] = None
    data_title_contains: Optional[str] = None
    statuses: Optional[List[AnnotationTaskStatus]] = None


class AnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.ANNOTATION] = WorkflowStageType.ANNOTATION

    """
    An Annotate stage in a non-Consensus Project.

    You can use this stage in Consensus and non-Consensus Projects.
    """

    def get_tasks(
        self,
        *,
        assignee: Union[List[str], str, None] = None,
        data_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        dataset_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        data_title: Optional[str] = None,
        status: Optional[AnnotationTaskStatus | List[AnnotationTaskStatus]] = None,
    ) -> Iterable[AnnotationTask]:
        """
        Retrieves tasks for the AnnotationStage.

        **Parameters**

        - `assignee` (Union[List[str], str, None]): A list of user emails or a single user email to filter tasks by assignee.
        - `data_hash` (Union[List[UUID], UUID, List[str], str, None]): A list of data unit UUIDs or a single data unit UUID to filter tasks by data hash.
        - `dataset_hash` (Union[List[UUID], UUID, List[str], str, None]): A list of dataset UUIDs or a single dataset UUID to filter tasks by dataset hash.
        - `data_title` (Optional[str]): A string to filter tasks by data title.
        - `status` (Optional[AnnotationTaskStatus | List[AnnotationTaskStatus]]): A status or a list of statuses to filter tasks by their status.

        **Returns**

        An iterable of `AnnotationTask` instances from both non-Consensus and Consensus Projects.
        """
        params = _AnnotationTasksQueryParams(
            user_emails=ensure_list(assignee),
            data_hashes=ensure_uuid_list(data_hash),
            dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_contains=data_title,
            statuses=ensure_list(status),
        )

        for task in self._workflow_client.get_tasks(self.uuid, params, type_=AnnotationTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self._workflow_client
            yield task


class _ActionSubmit(WorkflowAction):
    action: Literal["SUBMIT"] = "SUBMIT"
    resolve_label_reviews: bool = True


class _ActionAssign(WorkflowAction):
    action: Literal["ASSIGN"] = "ASSIGN"
    assignee: str


class _ActionRelease(WorkflowAction):
    action: Literal["RELEASE"] = "RELEASE"


class AnnotationTask(WorkflowTask):
    status: AnnotationTaskStatus
    data_hash: UUID
    data_title: str
    label_branch_name: str
    assignee: Optional[str]

    """
    Represents a task in a non-Consensus Annotate stage.

    **Attributes**

    - `status` (AnnotationTaskStatus): The current status of the task.
    - `data_hash` (UUID): Unique ID for the data unit.
    - `data_title` (str): Name of the data unit.
    - `label_branch_name` (str): Name of the label branch.
    - `assignee` (Optional[str]): User assigned to the task.

    **Allowed actions**

    - `submit`: Submits a task for review.
    - `assign`: Assigns a task to a user.
    - `release`: Releases a task from the current user.
    """

    def submit(self, *, bundle: Optional[Bundle] = None) -> None:
        """
        Submits the task for review.

        **Parameters**

        - `bundle` (Optional[Bundle]): Optional bundle to be included with the submission.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionSubmit(task_uuid=self.uuid), bundle=bundle)

    def assign(self, assignee: str, *, bundle: Optional[Bundle] = None) -> None:
        """
        Assigns the task to a user.

        **Parameters**

        - `assignee` (str): The email of the user to assign the task to.
        - `bundle` (Optional[Bundle]): Optional bundle to be included with the assignment.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionAssign(task_uuid=self.uuid, assignee=assignee), bundle=bundle)

    def release(self, *, bundle: Optional[Bundle] = None) -> None:
        """
        Releases the task from the current user.

        **Parameters**

        - `bundle` (Optional[Bundle]): Optional bundle to be included with the release.
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionRelease(task_uuid=self.uuid), bundle=bundle)
