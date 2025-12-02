"""---
title: "Final Stage"
slug: "sdk-ref-stage-final"
hidden: false
metadata:
  title: "Final Stage"
  description: "Encord SDK Final Stages: Complete and Archive."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from typing import Iterable, List, Literal, Optional, Union
from uuid import UUID

from encord.common.utils import ensure_uuid_list
from encord.http.bundle import Bundle
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowStageBase, WorkflowTask


class _FinalTasksQueryParams(TasksQueryParams):
    data_hashes: Optional[List[UUID]] = None
    dataset_hashes: Optional[List[UUID]] = None
    data_title_contains: Optional[str] = None


class FinalStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.DONE] = WorkflowStageType.DONE

    """
    Final stage for a task in Consensus and non-Consensus Projects. The final stages are COMPLETE or ARCHIVE.
    """

    def get_tasks(
        self,
        data_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        dataset_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        data_title: Optional[str] = None,
    ) -> Iterable[FinalStageTask]:
        """Retrieves tasks for the FinalStage.

        Args:
            data_hash: Unique ID(s) for the data unit(s).
            dataset_hash: Unique ID(s) for the dataset(s) that the data unit(s) belongs to.
            data_title: A string to filter tasks by the data unit's name.

        Returns:
            An iterable of `FinalStageTask` instances with the following information:
            - `uuid`: Unique identifier for the task.
            - `created_at`: Time and date the task was created.
            - `updated_at`: Time and date the task was last edited.
            - `data_hash`: Unique identifier for the data unit.
            - `data_title`: Name/title of the data unit.
        """
        params = _FinalTasksQueryParams(
            data_hashes=ensure_uuid_list(data_hash),
            dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_contains=data_title,
        )

        for task in self._workflow_client.get_tasks(self.uuid, params, type_=FinalStageTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self._workflow_client
            yield task


class FinalStageTask(WorkflowTask):
    """Represents tasks in a FinalStage, which are read-only and cannot be acted upon
    except for being moved programmatically.

    **Attributes**

    - `data_hash` (UUID): Unique ID for the data unit.
    - `data_title` (str): Name of the data unit.

    **Allowed actions**

    - `move`: Moves the task to another stage in the workflow.
    """

    data_hash: UUID
    data_title: str

    def move(self, *, destination_stage_uuid: UUID, bundle: Optional[Bundle] = None) -> None:
        """Moves the final stage task from its current stage to another stage.

        Args:
            destination_stage_uuid: Unique identifier of the stage to move the task to.
            bundle: Optional bundle of actions to execute with the move.

        Returns:
            None
        """
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.move(
            origin_stage_uuid=stage_uuid,
            destination_stage_uuid=destination_stage_uuid,
            task_uuids=[self.uuid],
            bundle=bundle,
        )
