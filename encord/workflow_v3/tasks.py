"""Native tasks, targets and assignment metadata."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Literal, Optional, Union
from uuid import UUID

from encord.orm.tasks_v3 import TargetType, TaskStatus
from encord.orm.workflow_v3 import StageType
from encord.workflow_v3._client import WorkflowClient


@dataclass(frozen=True)
class Target:
    """Target identity and scope, without labels, media or subset contents."""

    _client: WorkflowClient = field(repr=False, compare=False)
    id: UUID
    project_id: UUID
    dataset_hash: str
    created_at: datetime
    deleted_at: Optional[datetime]
    target_type: ClassVar[TargetType]


@dataclass(frozen=True)
class DataUnitTarget(Target):
    """An entire data unit, including a data group."""

    data_hash: str
    target_type: ClassVar[Literal[TargetType.DATA_UNIT]] = TargetType.DATA_UNIT


@dataclass(frozen=True)
class DataUnitSliceTarget(Target):
    """A named slice of one data unit; range contents are not embedded."""

    data_hash: str
    qualifier_name: str
    target_type: ClassVar[Literal[TargetType.DATA_UNIT_SLICE]] = TargetType.DATA_UNIT_SLICE


@dataclass(frozen=True)
class DatasetTarget(Target):
    """A whole dataset, without a single data-unit identifier."""

    target_type: ClassVar[Literal[TargetType.DATASET]] = TargetType.DATASET


@dataclass(frozen=True)
class DataGroupSubsetTarget(Target):
    """A named subset of a data group; member contents are not embedded."""

    data_hash: str
    qualifier_name: str
    target_type: ClassVar[Literal[TargetType.DATA_GROUP_SUBSET]] = TargetType.DATA_GROUP_SUBSET


@dataclass(frozen=True)
class DatasetSubsetTarget(Target):
    """A named dataset subset; member contents are not embedded."""

    qualifier_name: str
    target_type: ClassVar[Literal[TargetType.DATASET_SUBSET]] = TargetType.DATASET_SUBSET


@dataclass(frozen=True)
class UnknownTarget(Target):
    """An unfamiliar target type; specialized access may require an SDK upgrade."""

    raw_target_type: str
    target_type: ClassVar[Literal[TargetType.UNKNOWN]] = TargetType.UNKNOWN


TaskTarget = Union[
    DataUnitTarget, DataUnitSliceTarget, DatasetTarget, DataGroupSubsetTarget, DatasetSubsetTarget, UnknownTarget
]


@dataclass(frozen=True)
class Assignment:
    """Assignment snapshot; assigned_to and assigned_by are opaque user IDs, not emails."""

    assigned_to: Optional[str]
    assigned_by: Optional[str]
    assigned_at: Optional[datetime]


@dataclass(frozen=True)
class Task:
    """Read-only snapshot of one visit to a stage, identified separately from its target.

    Actions leave this snapshot unchanged; use workflow.get_task() to refresh it.
    Sent mutations are not automatically retried. A lost response may leave the
    outcome uncertain; a stale-task error does not establish an earlier success.
    """

    _client: WorkflowClient = field(repr=False, compare=False)
    id: UUID
    stage_id: UUID
    stage_type: StageType
    target: TaskTarget
    status: TaskStatus
    priority: float
    created_at: datetime
    entered_at: Optional[datetime]
    processing_at: Optional[datetime]
    done_at: Optional[datetime]
    canceled_at: Optional[datetime]
    assignment: Optional[Assignment]
    raw_stage_type: Optional[str] = None


@dataclass(frozen=True)
class ExternalTask(Task):
    """A task at an External stage."""

    def submit(self, *, pathway_id: Optional[Union[UUID, str]] = None, pathway_name: Optional[str] = None) -> None:
        """Submit an entered External task through an outgoing pathway.

        Select by ID or exact, case-sensitive name, not both. Omit both only when
        the stage has one outgoing pathway. Requires project management access.
        Unavailable tasks raise StaleTaskError. Leaves this snapshot unchanged;
        sent requests are not automatically retried.
        """
        from encord.workflow_v3._submission_actions import submit_task

        submit_task(self._client, self.id, pathway_id=pathway_id, pathway_name=pathway_name)


@dataclass(frozen=True)
class ManualTask(Task):
    """A task supporting manual assignment and release."""

    def assign(self, assignee: str) -> None:
        """Assign this task to an eligible user by email.

        Non-managers may assign only to themselves. Leaves this snapshot unchanged;
        sent requests are not automatically retried.
        """
        from encord.workflow_v3._assignment_actions import assign_task

        assign_task(self._client, self.id, assignee=assignee)

    def release(self) -> None:
        """Release this task's current assignment without completing or moving it.

        Requires project management access and acts on the current assignment,
        not this snapshot's holder. Releasing a valid unassigned task succeeds.
        Unavailable tasks raise StaleTaskError. Leaves this snapshot unchanged;
        sent requests are not automatically retried.
        """
        from encord.workflow_v3._assignment_actions import release_task

        release_task(self._client, self.id)


@dataclass(frozen=True)
class AnnotationTask(ManualTask):
    """A task at an Annotation stage."""

    def submit(
        self,
        *,
        pathway_id: Optional[Union[UUID, str]] = None,
        pathway_name: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        """Submit an Annotation task through an outgoing pathway; save labels separately first.

        Select by ID or exact, case-sensitive name, not both. Omit both only when
        the stage has one outgoing pathway. Non-managers must hold the assignment
        and remain eligible to work at the stage. Comments require a DataUnitTarget.
        Backend pathway rules apply. Leaves this snapshot unchanged; sent requests
        are not automatically retried.
        """
        from encord.workflow_v3._submission_actions import submit_task

        submit_task(self._client, self.id, pathway_id=pathway_id, pathway_name=pathway_name, comment=comment)


@dataclass(frozen=True)
class ReviewTask(ManualTask):
    """A task at a Review stage."""

    def submit(
        self,
        *,
        pathway_id: Optional[Union[UUID, str]] = None,
        pathway_name: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        """Submit through an outgoing pathway without changing individual label decisions.

        Select by ID or exact, case-sensitive name, not both. Omit both only when
        the stage has one outgoing pathway. Non-managers must hold the assignment
        and remain eligible to work at the stage. Comments require a DataUnitTarget.
        Backend pathway rules apply. Leaves this snapshot unchanged; sent requests
        are not automatically retried.
        """
        from encord.workflow_v3._submission_actions import submit_task

        submit_task(self._client, self.id, pathway_id=pathway_id, pathway_name=pathway_name, comment=comment)
