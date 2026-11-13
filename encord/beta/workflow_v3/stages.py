"""Stage types in a read-only workflow graph snapshot."""

from dataclasses import dataclass, field
from typing import ClassVar, Generic, Iterator, Literal, Optional, Sequence, Tuple, TypeVar, Union, cast
from uuid import UUID

from encord.beta.workflow_v3 import _submission_actions, _task_reads
from encord.beta.workflow_v3._client import WorkflowClient
from encord.beta.workflow_v3.pathways import Pathway
from encord.beta.workflow_v3.settings import (
    AnnotationStageSettingsV1,
    ArchiveStageSettingsV1,
    CollaboratorRouterStageSettingsV1,
    CompleteStageSettingsV1,
    ExternalStageSettingsV1,
    PercentageRouterStageSettingsV1,
    ReviewStageSettingsV1,
    Settings,
    SkipStageSettingsV1,
    StartStageSettingsV1,
    UnknownStageSettings,
)
from encord.beta.workflow_v3.tasks import AnnotationTask, ExternalTask, ReviewTask, Task
from encord.orm.tasks_v3 import TaskSort, TaskStatus
from encord.orm.workflow_v3 import StageType

SettingsT = TypeVar("SettingsT", bound=Settings)
TaskT = TypeVar("TaskT", bound=Task, covariant=True)


@dataclass(frozen=True, repr=False)
class Stage(Generic[SettingsT, TaskT]):
    """Identity and outgoing connections for one stage in the loaded graph."""

    _client: WorkflowClient = field(repr=False, compare=False)
    id: UUID
    name: str
    settings: SettingsT
    pathways: Tuple[Pathway, ...]
    stage_type: ClassVar[StageType]

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id='{self.id}', name={self.name!r})"

    def get_tasks(
        self, *, statuses: Optional[Sequence[TaskStatus]] = None, sort: Optional[TaskSort] = None
    ) -> Iterator[TaskT]:
        """Iterate permitted current tasks, fetching pages lazily without claiming work.

        Arguments are validated immediately; request errors may arise during iteration.
        This is a changing queue, not a snapshot.
        Terminal stages use newest-arrival ordering and do not accept filters.
        """
        return cast(
            Iterator[TaskT],
            _task_reads.list_tasks(self._client, self.id, statuses=statuses, sort=sort),
        )


@dataclass(frozen=True, repr=False)
class StartStage(Stage[Union[StartStageSettingsV1, UnknownStageSettings], Task]):
    """Background processing at workflow entry."""

    stage_type: ClassVar[Literal[StageType.START]] = StageType.START


@dataclass(frozen=True, repr=False)
class AnnotationStage(Stage[Union[AnnotationStageSettingsV1, UnknownStageSettings], AnnotationTask]):
    """Manual annotation of targets."""

    stage_type: ClassVar[Literal[StageType.ANNOTATION]] = StageType.ANNOTATION

    def submit_tasks(
        self,
        tasks: Sequence[Task],
        *,
        pathway_id: Optional[Union[UUID, str]] = None,
        pathway_name: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        """Submit up to 100 tasks atomically through one pathway with an optional comment, without replaying sent requests."""
        _submission_actions.submit_tasks(
            self._client,
            self.id,
            [task.id for task in tasks],
            pathway_id=pathway_id,
            pathway_name=pathway_name,
            comment=comment,
        )


@dataclass(frozen=True, repr=False)
class ReviewStage(Stage[Union[ReviewStageSettingsV1, UnknownStageSettings], ReviewTask]):
    """Manual review of targets and labels."""

    stage_type: ClassVar[Literal[StageType.REVIEW]] = StageType.REVIEW

    def submit_tasks(
        self,
        tasks: Sequence[Task],
        *,
        pathway_id: Optional[Union[UUID, str]] = None,
        pathway_name: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        """Submit up to 100 tasks atomically without changing individual label decisions.

        One pathway and optional comment apply to every task. Sent requests are not replayed.
        """
        _submission_actions.submit_tasks(
            self._client,
            self.id,
            [task.id for task in tasks],
            pathway_id=pathway_id,
            pathway_name=pathway_name,
            comment=comment,
        )


@dataclass(frozen=True, repr=False)
class ExternalStage(Stage[Union[ExternalStageSettingsV1, UnknownStageSettings], ExternalTask]):
    """Work held for an external integration."""

    stage_type: ClassVar[Literal[StageType.EXTERNAL]] = StageType.EXTERNAL

    def submit_tasks(
        self,
        tasks: Sequence[Task],
        *,
        pathway_id: Optional[Union[UUID, str]] = None,
        pathway_name: Optional[str] = None,
    ) -> None:
        """Submit up to 100 tasks atomically through one pathway, without replaying sent requests."""
        _submission_actions.submit_tasks(
            self._client,
            self.id,
            [task.id for task in tasks],
            pathway_id=pathway_id,
            pathway_name=pathway_name,
        )


@dataclass(frozen=True, repr=False)
class CompleteStage(Stage[Union[CompleteStageSettingsV1, UnknownStageSettings], Task]):
    """Terminal stage for the Complete outcome."""

    stage_type: ClassVar[Literal[StageType.COMPLETE]] = StageType.COMPLETE


@dataclass(frozen=True, repr=False)
class ArchiveStage(Stage[Union[ArchiveStageSettingsV1, UnknownStageSettings], Task]):
    """Terminal stage for the Archive outcome."""

    stage_type: ClassVar[Literal[StageType.ARCHIVE]] = StageType.ARCHIVE


@dataclass(frozen=True, repr=False)
class SkipStage(Stage[Union[SkipStageSettingsV1, UnknownStageSettings], Task]):
    """Terminal stage for the Skip outcome."""

    stage_type: ClassVar[Literal[StageType.SKIP]] = StageType.SKIP


@dataclass(frozen=True, repr=False)
class PercentageRouterStage(Stage[Union[PercentageRouterStageSettingsV1, UnknownStageSettings], Task]):
    """Targets are routed by the configured pathway allocations."""

    stage_type: ClassVar[Literal[StageType.PERCENTAGE_ROUTER]] = StageType.PERCENTAGE_ROUTER


@dataclass(frozen=True, repr=False)
class CollaboratorRouterStage(Stage[Union[CollaboratorRouterStageSettingsV1, UnknownStageSettings], Task]):
    """Route targets using the user who last processed them at a manual stage."""

    stage_type: ClassVar[Literal[StageType.COLLABORATOR_ROUTER]] = StageType.COLLABORATOR_ROUTER


@dataclass(frozen=True, repr=False)
class UnknownStage(Stage[UnknownStageSettings, Task]):
    """An unfamiliar stage available for discovery, not specialized operations."""

    raw_stage_type: str
    stage_type: ClassVar[Literal[StageType.UNKNOWN]] = StageType.UNKNOWN


WorkflowStage = Union[
    StartStage,
    AnnotationStage,
    ReviewStage,
    ExternalStage,
    CompleteStage,
    ArchiveStage,
    SkipStage,
    PercentageRouterStage,
    CollaboratorRouterStage,
    UnknownStage,
]
