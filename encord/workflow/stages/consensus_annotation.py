from __future__ import annotations

from typing import Iterable, List, Literal
from uuid import UUID

from encord.orm.base_dto import Field
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import WorkflowStageBase, WorkflowTask
from encord.workflow.stages.annotation import AnnotationTask


class ConsensusAnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_ANNOTATION] = WorkflowStageType.CONSENSUS_ANNOTATION

    def get_tasks(self) -> Iterable[ConsensusAnnotationTask]:
        for task in self._workflow_client.get_tasks(self.uuid, type_=ConsensusAnnotationTask):
            for subtask in task.subtasks:
                subtask._stage_uuid = self.uuid
                subtask._workflow_client = self._workflow_client
            yield task


class ConsensusAnnotationTask(WorkflowTask):
    data_hash: UUID
    data_title: str
    subtasks: List[AnnotationTask] = Field(default_factory=list)
