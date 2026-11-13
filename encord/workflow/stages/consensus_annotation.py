"""---
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
from encord.http.bundle import Bundle
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
        """Returns the tasks in this Consensus Annotate stage that match the given filters.

        All filters are optional. If you pass several, only tasks that match all of them are returned.

        Args:
            assignee: Only return tasks assigned to this user, or to any of these users. Pass user emails.
            data_hash: Only return tasks for this data unit, or for any of these data units.
            dataset_hash: Only return tasks for data units in this dataset, or in any of these datasets.
            data_title: Only return tasks whose data unit title contains this text.

        Returns:
            Iterable[ConsensusAnnotationTask]: The matching tasks. Tasks are fetched page by page as you iterate. Each
                task's `subtasks` are the `AnnotationTask` instances of its annotators.
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

            task._stage_uuid = self.uuid
            task._workflow_client = self._workflow_client
            yield task


class ConsensusAnnotationTask(WorkflowTask):
    """Represents tasks in the Annotate stage of a Consensus Project.

    **Attributes**

    - `data_hash` (UUID): Unique ID for the data unit.
    - `data_title` (str): Name of the data unit.
    - `subtasks` (List[AnnotationTask]): List of tasks from individual annotators in a Consensus Project.

    **Allowed actions**

    - `move`: Moves the consensus annotation task to another stage in the workflow.
    """

    data_hash: UUID
    data_title: str
    subtasks: List[AnnotationTask] = Field(default_factory=list)

    def move(self, *, destination_stage_uuid: UUID, bundle: Optional[Bundle] = None) -> None:
        """Moves the Consensus Annotate task directly to another stage in the Workflow.

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
