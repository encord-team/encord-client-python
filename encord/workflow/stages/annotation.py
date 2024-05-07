from __future__ import annotations

from typing import Iterable, Literal, Optional

from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import WorkflowAction, WorkflowStageBase, WorkflowTask


class AnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.ANNOTATION] = WorkflowStageType.ANNOTATION

    def get_tasks(self) -> Iterable[AnnotationTask]:
        for task in self.workflow_client.get_tasks(self.uuid, type_=AnnotationTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self.workflow_client
            yield task


class _ActionSubmit(WorkflowAction):
    action: Literal["SUBMIT"] = "SUBMIT"


class _ActionAssign(WorkflowAction):
    action: Literal["ASSIGN"] = "ASSIGN"
    assignee: str


class _ActionRelease(WorkflowAction):
    action: Literal["RELEASE"] = "RELEASE"


class AnnotationTask(WorkflowTask):
    assignee: Optional[str]
    label_branch_name: str

    def submit(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionSubmit(task_uuid=self.uuid))

    def assign(self, assignee: str) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionAssign(task_uuid=self.uuid, assignee=assignee))

    def release(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionRelease(task_uuid=self.uuid))
