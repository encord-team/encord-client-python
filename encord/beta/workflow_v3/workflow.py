"""Local discovery of the complete workflow graph."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Tuple, Type, TypeVar, Union, cast, overload
from uuid import UUID

from encord.beta.workflow_v3 import _assignment_actions, _task_reads, settings
from encord.beta.workflow_v3._client import WorkflowClient
from encord.beta.workflow_v3.pathways import Pathway
from encord.beta.workflow_v3.stages import (
    AnnotationStage,
    ArchiveStage,
    CollaboratorRouterStage,
    CompleteStage,
    ExternalStage,
    PercentageRouterStage,
    ReviewStage,
    SkipStage,
    Stage,
    StartStage,
    UnknownStage,
    WorkflowStage,
)
from encord.beta.workflow_v3.tasks import Task
from encord.orm import workflow_v3 as dto

if TYPE_CHECKING:
    from encord.http.v2.api_client import ApiClient


StageT = TypeVar("StageT", bound=Stage)
SettingsT = TypeVar("SettingsT", bound=settings.StageSettings)


def _empty_settings(
    value: Union[dto.EmptySettingsDTO, dto.UnknownSettingsDTO], settings_type: Type[SettingsT]
) -> Union[SettingsT, settings.UnknownStageSettings]:
    if isinstance(value, dto.UnknownSettingsDTO):
        return settings.UnknownStageSettings(value.values)
    return settings_type()


def _construct_pathway(pathway: dto.PathwayDTO) -> Pathway:
    return Pathway(
        id=pathway.id,
        name=pathway.name,
        source_stage_id=pathway.source_stage_id,
        destination_stage_id=pathway.destination_stage_id,
        verdict=pathway.verdict,
    )


def _construct_stage(
    client: WorkflowClient, stage: "dto.WorkflowStageDTO", pathways: Tuple[Pathway, ...]
) -> WorkflowStage:
    if isinstance(stage, dto.StartStageDTO):
        return StartStage(
            client, stage.id, stage.name, _empty_settings(stage.settings, settings.StartStageSettingsV1), pathways
        )
    elif isinstance(stage, dto.AnnotationStageDTO):
        return AnnotationStage(
            client, stage.id, stage.name, _empty_settings(stage.settings, settings.AnnotationStageSettingsV1), pathways
        )
    elif isinstance(stage, dto.ReviewStageDTO):
        return ReviewStage(
            client, stage.id, stage.name, _empty_settings(stage.settings, settings.ReviewStageSettingsV1), pathways
        )
    elif isinstance(stage, dto.ExternalStageDTO):
        return ExternalStage(
            client, stage.id, stage.name, _empty_settings(stage.settings, settings.ExternalStageSettingsV1), pathways
        )
    elif isinstance(stage, dto.CompleteStageDTO):
        return CompleteStage(
            client, stage.id, stage.name, _empty_settings(stage.settings, settings.CompleteStageSettingsV1), pathways
        )
    elif isinstance(stage, dto.ArchiveStageDTO):
        return ArchiveStage(
            client, stage.id, stage.name, _empty_settings(stage.settings, settings.ArchiveStageSettingsV1), pathways
        )
    elif isinstance(stage, dto.SkipStageDTO):
        return SkipStage(
            client, stage.id, stage.name, _empty_settings(stage.settings, settings.SkipStageSettingsV1), pathways
        )
    elif isinstance(stage, dto.PercentageRouterStageDTO):
        return PercentageRouterStage(
            client,
            stage.id,
            stage.name,
            settings.UnknownStageSettings(stage.settings.values)
            if isinstance(stage.settings, dto.UnknownSettingsDTO)
            else settings.PercentageRouterStageSettingsV1(stage.settings.pathway_probabilities),
            pathways,
        )
    elif isinstance(stage, dto.CollaboratorRouterStageDTO):
        return CollaboratorRouterStage(
            client,
            stage.id,
            stage.name,
            _empty_settings(stage.settings, settings.CollaboratorRouterStageSettingsV1),
            pathways,
        )
    elif isinstance(stage, dto.UnknownStageDTO):
        return UnknownStage(
            client, stage.id, stage.name, settings.UnknownStageSettings(stage.settings), pathways, stage.stage_type
        )
    else:
        raise TypeError(f"Unsupported stage response: {type(stage).__name__}")


class Workflow:
    """Read-only graph snapshot loaded with the project.

    Discovery is local. Refresh the project to load a new graph snapshot.
    """

    def __init__(self, api_client: "ApiClient", project_id: UUID, workflow: "dto.WorkflowV3DTO") -> None:
        self._client = WorkflowClient(api_client, project_id)
        self._id = workflow.id
        self._pathways = tuple(_construct_pathway(pathway) for pathway in workflow.pathways)
        outgoing: Dict[UUID, List[Pathway]] = defaultdict(list)
        for pathway in self._pathways:
            outgoing[pathway.source_stage_id].append(pathway)
        self._stages = tuple(
            _construct_stage(self._client, stage, tuple(outgoing.get(stage.id, ()))) for stage in workflow.stages
        )
        self._stages_by_id = {stage.id: stage for stage in self._stages}

    @property
    def id(self) -> UUID:
        """Workflow identifier."""
        return self._id

    @property
    def stages(self) -> Tuple[WorkflowStage, ...]:
        """Every stage, including Start, routers and all terminal outcomes."""
        return self._stages

    @property
    def pathways(self) -> Tuple[Pathway, ...]:
        """All connections, in the order returned by the backend."""
        return self._pathways

    def get_task(self, *, id: Union[UUID, str]) -> "Task":
        """Fetch one current or historical task, subject to backend read permissions."""
        return _task_reads.get_task(self._client, id)

    def release_tasks(self, tasks: Sequence[Task]) -> None:
        """Release up to 1000 assignments and claims atomically; unavailable tasks raise StaleTaskError.

        Already-unassigned tasks succeed. Sent requests are not replayed automatically.
        """
        _assignment_actions.release_tasks(self._client, [task.id for task in tasks])

    @overload
    def get_stage(
        self,
        *,
        name: Optional[str] = None,
        id: Optional[Union[UUID, str]] = None,
        type_: Type[StageT],
    ) -> StageT: ...

    @overload
    def get_stage(
        self,
        *,
        name: Optional[str] = None,
        id: Optional[Union[UUID, str]] = None,
        type_: None = None,
    ) -> WorkflowStage: ...

    def get_stage(
        self,
        *,
        name: Optional[str] = None,
        id: Optional[Union[UUID, str]] = None,
        type_: Optional[Type[StageT]] = None,
    ) -> Union[WorkflowStage, StageT]:
        """Find a stage by exact name or ID.

        Args:
            name: Exact name. Duplicate names require ID lookup.
            id: Unique stage identifier, as a UUID or string.
            type_: Expected stage class, also used for return-type narrowing.

        Raises:
            ValueError: Selectors are missing, conflicting, ambiguous, malformed or unmatched.
            TypeError: The matching stage is not of the requested type.
        """
        if (name is None) == (id is None):
            raise ValueError("Provide exactly one of name or id.")

        if id is not None:
            try:
                stage_id = id if isinstance(id, UUID) else UUID(id)
            except ValueError as error:
                raise ValueError(f"Invalid stage ID: {id!r}.") from error
            stage = self._stages_by_id.get(stage_id)
            if stage is None:
                raise ValueError(f"No matching stage found: '{id}' in workflow '{self.id}'.")
        else:
            matches = [candidate for candidate in self._stages if candidate.name == name]
            if not matches:
                raise ValueError(f"No matching stage found: '{name}' in workflow '{self.id}'.")
            if len(matches) > 1:
                stage_ids = ", ".join(str(match.id) for match in matches)
                raise ValueError(
                    f"Several stages have the name '{name}' in workflow '{self.id}'; use one of their IDs: {stage_ids}."
                )
            stage = matches[0]

        if type_ is not None:
            if not isinstance(stage, type_):
                raise TypeError(
                    f"Expected '{type_.__name__}' but got '{type(stage).__name__}' "
                    f"for stage '{stage.name}' ({stage.id}) in workflow '{self.id}'."
                )
            return cast(StageT, stage)
        return stage
