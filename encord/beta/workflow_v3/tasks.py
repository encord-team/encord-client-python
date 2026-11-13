"""Native tasks, targets and assignment metadata."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Optional, Union
from uuid import UUID

from encord.beta.workflow_v3._client import WorkflowClient
from encord.orm.tasks_v3 import TaskStatus
from encord.orm.workflow_v3 import StageType


@dataclass(frozen=True)
class Target:
    """Target identity and scope, without labels, media or subset contents."""

    _client: WorkflowClient = field(repr=False, compare=False)
    id: UUID
    project_id: UUID
    dataset_hash: str
    created_at: datetime
    deleted_at: Optional[datetime]


@dataclass(frozen=True)
class DataUnitTarget(Target):
    """An entire data unit, including a data group."""

    data_hash: str
    target_type: ClassVar[str] = "data_unit"


@dataclass(frozen=True)
class DataUnitSliceTarget(Target):
    """A named slice of one data unit; range contents are not embedded."""

    data_hash: str
    qualifier_name: str
    target_type: ClassVar[str] = "data_unit_slice"


@dataclass(frozen=True)
class DatasetTarget(Target):
    """A whole dataset, without a single data-unit identifier."""

    target_type: ClassVar[str] = "dataset"


@dataclass(frozen=True)
class DataGroupSubsetTarget(Target):
    """A named subset of a data group; member contents are not embedded."""

    data_hash: str
    qualifier_name: str
    target_type: ClassVar[str] = "data_group_subset"


@dataclass(frozen=True)
class DatasetSubsetTarget(Target):
    """A named dataset subset; member contents are not embedded."""

    qualifier_name: str
    target_type: ClassVar[str] = "dataset_subset"


@dataclass(frozen=True)
class UnknownTarget(Target):
    """An unfamiliar target type; specialized access may require an SDK upgrade."""

    raw_target_type: str
    target_type: ClassVar[str] = "_UNKNOWN_"


TaskTarget = Union[
    DataUnitTarget, DataUnitSliceTarget, DatasetTarget, DataGroupSubsetTarget, DatasetSubsetTarget, UnknownTarget
]


@dataclass(frozen=True)
class Assignment:
    """User assignment information, separate from task lifecycle."""

    assigned_to: Optional[str]
    assigned_by: Optional[str]
    assigned_at: Optional[datetime]


@dataclass(frozen=True)
class Task:
    """One operation on a target at a stage, identified separately from the target."""

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
        """Submit an entered External task, optionally selecting an outgoing pathway.

        Select an outgoing pathway by ID or exact, case-sensitive name, not both.
        With neither supplied, the stage must have exactly one outgoing pathway.
        Requires project management access. Success returns None and leaves this
        snapshot unchanged. A stale task raises StaleTaskError.
        Requests are not replayed after sending; a transport failure may leave
        the outcome uncertain. Backend validation determines action eligibility.
        """
        from encord.beta.workflow_v3._submission_actions import submit_task

        submit_task(self._client, self.id, pathway_id=pathway_id, pathway_name=pathway_name)


@dataclass(frozen=True)
class ManualTask(Task):
    """A task supporting manual assignment and release."""

    def assign(self, assignee: str) -> None:
        """Assign this task to an eligible user by email, leaving this snapshot unchanged."""
        from encord.beta.workflow_v3._assignment_actions import assign_task

        assign_task(self._client, self.id, assignee=assignee)

    def release(self) -> None:
        """Release this task's current assignment and claim without completing or moving it.

        Requires project management access and acts on the current assignment, not this snapshot's holder.
        Releasing an unassigned task succeeds and clears any claim.
        Success leaves this snapshot unchanged.
        """
        from encord.beta.workflow_v3._assignment_actions import release_task

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
        """Submit saved work through an outgoing pathway, leaving this snapshot unchanged.

        Select by ID or exact name, or omit both when the stage has exactly one outgoing pathway.
        Backend validation and permissions apply. Sent requests are not replayed.
        """
        from encord.beta.workflow_v3._submission_actions import submit_task

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

        Native permissions and pathway rules apply. Success returns None and leaves
        this snapshot unchanged. Sent requests are not replayed.
        """
        from encord.beta.workflow_v3._submission_actions import submit_task

        submit_task(self._client, self.id, pathway_id=pathway_id, pathway_name=pathway_name, comment=comment)
