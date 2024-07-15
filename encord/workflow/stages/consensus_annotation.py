"""
---
title: "Consensus Annotation Stage"
slug: "sdk-ref-stage-consen-annotation"
hidden: false
metadata:
  title: "Consensus Annotation Stage"
  description: "Encord SDK Consensus Annotation Stage."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from typing import Iterable, List, Literal, Optional, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.orm.base_dto import Field
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowStageBase, WorkflowTask
from encord.workflow.stages.annotation import AnnotationTask


class _AnnotationTasksQueryParams(TasksQueryParams):
    user_emails: Optional[List[str]] = None
    data_hashes: Optional[List[UUID]] = None
    dataset_hashes: Optional[List[UUID]] = None
    data_title_contains: Optional[str] = None


class ConsensusAnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_ANNOTATION] = WorkflowStageType.CONSENSUS_ANNOTATION

    """
    The Annotate stage in a Consensus Project.
    """

    def get_tasks(
        self,
        *,
        assignee: Union[List[str], str, None] = None,
        data_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        dataset_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        data_title: Optional[str] = None,
    ) -> Iterable[ConsensusAnnotationTask]:
        """
        Retrieves tasks for the ConsensusAnnotationStage.

        **Parameters**

        - `assignee` (Union[List[str], str, None]): A list of user emails or a single user email to filter tasks by assignee.
        - `data_hash` (Union[List[UUID], UUID, List[str], str, None]): A list of data unit UUIDs or a single data unit UUID to filter tasks by data hash.
        - `dataset_hash` (Union[List[UUID], UUID, List[str], str, None]): A list of dataset UUIDs or a single dataset UUID to filter tasks by dataset hash.
        - `data_title` (Optional[str]): A string to filter tasks by data title.

        **Returns**

        An iterable of `ConsensusAnnotationTask` instances with the following information:
        - `uuid`: Unique identifier for the task.
        - `created_at`: Time and date the task was created.
        - `updated_at`: Time and date the task was last edited.
        - `data_hash`: Unique identifier for the data unit.
        - `data_title`: Name/title of the data unit.
        - `subtasks`: A list of subtasks that follow the task format for `AnnotationTask`.
        """
        params = _AnnotationTasksQueryParams(
            user_emails=ensure_list(assignee),
            data_hashes=ensure_uuid_list(data_hash),
            dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_contains=data_title,
        )

        for task in self._workflow_client.get_tasks(self.uuid, params, type_=ConsensusAnnotationTask):
            for subtask in task.subtasks:
                subtask._stage_uuid = self.uuid
                subtask._workflow_client = self._workflow_client
            yield task


class ConsensusAnnotationTask(WorkflowTask):
    """
    Represents tasks in the Annotate stage of a Consensus Project.

    **Attributes**

    - `data_hash` (UUID): Unique ID for the data unit.
    - `data_title` (str): Name of the data unit.
    - `subtasks` (List[AnnotationTask]): List of tasks from individual annotators in a Consensus Project.
    """

    data_hash: UUID
    data_title: str
    subtasks: List[AnnotationTask] = Field(default_factory=list)
