from __future__ import annotations

from enum import Enum, auto
from typing import Iterable, List, Literal, Optional, TypeVar, Union
from uuid import UUID

from encord.common.utils import ensure_list, ensure_uuid_list
from encord.http.bundle import Bundle
from encord.orm.base_dto import BaseDTO
from encord.orm.workflow import WorkflowStageType
from encord.workflow.common import TasksQueryParams, WorkflowAction, WorkflowStageBase, WorkflowTask


class AgentTaskStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    RELEASED = "RELEASED"
    SKIPPED = "SKIPPED"
    REOPENED = "REOPENED"
    COMPLETED = "COMPLETED"


class _ActionPathway(WorkflowAction):
    action: Literal["PATHWAY_ACTION"] = "PATHWAY_ACTION"
    pathway_uuid: Optional[str] = None
    pathway_name: Optional[str] = None


class AgentTask(WorkflowTask):
    status: AgentTaskStatus
    data_hash: UUID
    data_title: str
    label_branch_name: str
    assignee: Optional[str]

    """
    Represents a task in an Agent stage.

    **Attributes**

    - `status` (AgentTaskStatus): The current status of the task.
    - `data_hash` (UUID): Unique ID for the data unit.
    - `data_title` (str): Name of the data unit.
    - `label_branch_name` (str): Name of the label branch.
    - `assignee` (Optional[str]): User assigned to the task.

    **Allowed actions**

    ...
    """

    def proceed(
        self, pathway_name: str | None = None, pathway_uuid: str | None = None, *, bundle: Optional[Bundle] = None
    ) -> None:
        if not pathway_name and not pathway_uuid:
            raise ValueError("Either `pathway_name` or `pathway_uuid` parameter must be provided.")

        workflow_client, stage_uuid = self._get_client_data()
        workflow_client.action(
            stage_uuid,
            _ActionPathway(task_uuid=self.uuid, pathway_name=pathway_name, pathway_uuid=pathway_uuid),
            bundle=bundle,
        )


class _AgentTasksQueryParams(TasksQueryParams):
    user_emails: Optional[List[str]] = None
    data_hashes: Optional[List[UUID]] = None
    dataset_hashes: Optional[List[UUID]] = None
    data_title_contains: Optional[str] = None
    statuses: Optional[List[AgentTaskStatus]] = None


class AgentStage(WorkflowStageBase):
    stage_type: Literal[WorkflowStageType.AGENT] = WorkflowStageType.AGENT

    """
    An Agent stage.
    """

    def get_tasks(
        self,
        *,
        assignee: Union[List[str], str, None] = None,
        data_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        dataset_hash: Union[List[UUID], UUID, List[str], str, None] = None,
        data_title: Optional[str] = None,
        status: Optional[AgentTaskStatus | List[AgentTaskStatus]] = None,
    ) -> Iterable[AgentTask]:
        """
        Retrieves tasks for the AgentStage.

        **Parameters**

        - `assignee` (Union[List[str], str, None]): A list of user emails or a single user email to filter tasks by assignee.
        - `data_hash` (Union[List[UUID], UUID, List[str], str, None]): A list of data unit UUIDs or a single data unit UUID to filter tasks by data hash.
        - `dataset_hash` (Union[List[UUID], UUID, List[str], str, None]): A list of dataset UUIDs or a single dataset UUID to filter tasks by dataset hash.
        - `data_title` (Optional[str]): A string to filter tasks by data title.
        - `status` (Optional[AnnotationTaskStatus | List[AnnotationTaskStatus]]): A status or a list of statuses to filter tasks by their status.

        **Returns**

        An iterable of `AnnotationTask` instances from both non-Consensus and Consensus Projects.
        """
        params = _AgentTasksQueryParams(
            user_emails=ensure_list(assignee),
            data_hashes=ensure_uuid_list(data_hash),
            dataset_hashes=ensure_uuid_list(dataset_hash),
            data_title_contains=data_title,
            statuses=ensure_list(status),
        )

        for task in self._workflow_client.get_tasks(self.uuid, params, type_=AgentTask):
            task._stage_uuid = self.uuid
            task._workflow_client = self._workflow_client
            yield task
