"""
---
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

from encord.common.utils import ensure_list, ensure_uuid_list
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
        params = _FinalTasksQueryParams(
            data_hashes=ensure_uuid_list(data_hash),
            dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_contains=data_title,
        )

        """
        **Parameters**

        - data_hash: Unique ID for the data unit.
        - dataset_hash: Unique ID for the dataset that the data unit belongs to.
        - data_title: Name of the data unit.

        **Returns**

        Returns a list of tasks (see `FinalStageTask` class) in the stage with the following information:

        - uuid: Unique identifier for the task.
        - created_at: Time and date the task was created.
        - updated_at: Time and date the task was last edited.
        - data_hash: Unique identifier for the data unit.
        - data_title: Name/title of the data unit.
        """
        yield from self._workflow_client.get_tasks(self.uuid, params, type_=FinalStageTask)


class FinalStageTask(WorkflowTask):
    data_hash: UUID
    data_title: str

    """
    Tasks in a FinalStage can only be queried. No actions can be taken on the task.

    **Parameters**

    - dataset_hash: Unique ID for the dataset that the data unit belongs to.
    - data_title: Name of the data unit.
    """
