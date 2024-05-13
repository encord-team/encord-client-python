from __future__ import annotations

from typing import Iterable, List, Literal, Optional, TypeVar, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.orm.base_dto import BaseDTO
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowAction, WorkflowStageBase, WorkflowTask


class _AnnotationTasksQueryParams(TasksQueryParams):
    filter_user_emails: Optional[List[str]] = None
    filter_data_hashes: Optional[List[UUID]] = None
    filter_dataset_hashes: Optional[List[UUID]] = None
    data_title_like: Optional[str] = None


class AnnotationStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.ANNOTATION] = WorkflowStageType.ANNOTATION

    def get_tasks(
        self,
        *,
        assignee: Union[List[str], str, None] = None,
        data_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        dataset_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        data_title: Optional[str] = None,
    ) -> Iterable[AnnotationTask]:
        params = _AnnotationTasksQueryParams(
            filter_user_emails=ensure_list(assignee),
            filter_data_hashes=ensure_uuid_list(data_hash),
            filter_dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_like=data_title,
        )

        for task in self._workflow_client.get_tasks(self.uuid, params, type_=AnnotationTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self._workflow_client
            yield task


class _ActionSubmit(WorkflowAction):
    action: Literal["SUBMIT"] = "SUBMIT"


class _ActionAssign(WorkflowAction):
    action: Literal["ASSIGN"] = "ASSIGN"
    assignee: str


class _ActionRelease(WorkflowAction):
    action: Literal["RELEASE"] = "RELEASE"


class AnnotationTask(WorkflowTask):
    data_hash: UUID
    data_title: str
    label_branch_name: str
    assignee: Optional[str]

    def submit(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionSubmit(task_uuid=self.uuid))

    def assign(self, assignee: str) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionAssign(task_uuid=self.uuid, assignee=assignee))

    def release(self) -> None:
        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(stage_uuid, _ActionRelease(task_uuid=self.uuid))
