from enum import Enum, auto
from typing import Iterable
from uuid import UUID


class Task:
    task_uuid: UUID


class WorkflowNodeType(str, Enum):
    ANNOTATION = auto()


class WorkflowNode:
    node_type: WorkflowNodeType
    title: str


class WorkflowStage:
    def get_tasks(self) -> Iterable[Task]:
        return []

    def submit(self, task: Task) -> None:
        return


class Workflow:
    nodes: list[WorkflowNode]

    def get_stage(self, *, name: str | None = None, uuid: UUID | None = None) -> WorkflowStage:
        return WorkflowStage()
