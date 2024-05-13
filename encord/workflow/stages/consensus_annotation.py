from __future__ import annotations

from typing import Iterable, List, Literal, Optional, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.orm.base_dto import Field
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowStageBase, WorkflowTask
from encord.workflow.stages.annotation import AnnotationTask


class _AnnotationTasksQueryParams(TasksQueryParams):
    filter_user_emails: Optional[List[str]] = None
    filter_data_hashes: Optional[List[UUID]] = None
    filter_dataset_hashes: Optional[List[UUID]] = None
    data_title_like: Optional[str] = None


class ConsensusAnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_ANNOTATION] = WorkflowStageType.CONSENSUS_ANNOTATION

    def get_tasks(
        self,
        *,
        assignee: Union[List[str], str, None] = None,
        data_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        dataset_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        data_title: Optional[str] = None,
    ) -> Iterable[ConsensusAnnotationTask]:
        params = _AnnotationTasksQueryParams(
            filter_user_emails=ensure_list(assignee),
            filter_data_hashes=ensure_uuid_list(data_hash),
            filter_dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_like=data_title,
        )

        for task in self._workflow_client.get_tasks(self.uuid, params, type_=ConsensusAnnotationTask):
            for subtask in task.subtasks:
                subtask._stage_uuid = self.uuid
                subtask._workflow_client = self._workflow_client
            yield task


class ConsensusAnnotationTask(WorkflowTask):
    data_hash: UUID
    data_title: str
    subtasks: List[AnnotationTask] = Field(default_factory=list)
