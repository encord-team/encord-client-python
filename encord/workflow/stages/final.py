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
        """
        Retrieves tasks for the FinalStage.

        **Parameters**

        - `data_hash` (Union[List[UUID], UUID, List[str], str, None]): Unique ID(s) for the data unit(s).
        - `dataset_hash` (Union[List[UUID], UUID, List[str], str, None]): Unique ID(s) for the dataset(s) that the data unit(s) belongs to.
        - `data_title` (Optional[str]): A string to filter tasks by the data unit's name.

        **Returns**

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

        yield from self._workflow_client.get_tasks(self.uuid, params, type_=FinalStageTask)


class FinalStageTask(WorkflowTask):
    data_hash: UUID
    data_title: str

    """
    Represents tasks in a FinalStage, which can only be queried. No actions can be taken on the task.

    **Attributes**

    - `data_hash` (UUID): Unique ID for the data unit.
    - `data_title` (str): Name of the data unit.
    """
