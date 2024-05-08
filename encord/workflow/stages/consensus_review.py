from __future__ import annotations

from typing import Iterable, List, Literal, Optional
from uuid import UUID

from encord.orm.base_dto import BaseDTO
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import WorkflowAction, WorkflowStageBase, WorkflowTask


class ConsensusReviewStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.CONSENSUS_REVIEW] = WorkflowStageType.CONSENSUS_REVIEW

    def get_tasks(self) -> Iterable[ConsensusReviewTask]:
        for task in self.workflow_client.get_tasks(self.uuid, type_=ConsensusReviewTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self.workflow_client
            yield task


class _ActionApprove(WorkflowAction):
    action: Literal["APPROVE"] = "APPROVE"


class _ActionReject(WorkflowAction):
    action: Literal["REJECT"] = "REJECT"


class _ActionAssign(WorkflowAction):
    action: Literal["ASSIGN"] = "ASSIGN"
    assignee: str


class _ActionRelease(WorkflowAction):
    action: Literal["RELEASE"] = "RELEASE"


class ConsensusReviewOption(BaseDTO):
    annotator: str
    label_branch_name: str
    label_hash: Optional[UUID]


class ConsensusReviewTask(WorkflowTask):
    assignee: Optional[str]
    data_hash: UUID
    data_title: str
    options: List[ConsensusReviewOption]

    def approve(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionApprove(task_uuid=self.uuid))

    def reject(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionReject(task_uuid=self.uuid))

    def assign(self, assignee: str) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionAssign(task_uuid=self.uuid, assignee=assignee))

    def release(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionRelease(task_uuid=self.uuid))
