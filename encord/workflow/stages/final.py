from __future__ import annotations

from typing import Iterable, Literal
from uuid import UUID

from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import WorkflowStageBase, WorkflowTask


class FinalStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.DONE] = WorkflowStageType.DONE

    def get_tasks(self) -> Iterable[FinalStageTask]:
        yield from self._workflow_client.get_tasks(self.uuid, type_=FinalStageTask)


class FinalStageTask(WorkflowTask):
    data_hash: UUID
    data_title: str
