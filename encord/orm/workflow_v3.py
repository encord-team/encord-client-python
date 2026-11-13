"""Project response models for the workflow_v3 interface."""

from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Literal, Optional, Tuple, Union
from uuid import UUID

from pydantic import model_serializer

from encord.orm.base_dto import BaseDTO, Field, dto_validator

if TYPE_CHECKING:
    from pydantic import ConfigDict


class ReadEnum(str, Enum):
    """An extensible response enum; UNKNOWN is not a request value."""

    @classmethod
    def _missing_(cls, value: object) -> Optional["ReadEnum"]:
        if isinstance(value, str):
            return cls.__members__["UNKNOWN"]
        return None


class StageType(ReadEnum):
    START = "START"
    ANNOTATION = "ANNOTATION"
    REVIEW = "REVIEW"
    EXTERNAL = "EXTERNAL"
    COMPLETE = "COMPLETE"
    ARCHIVE = "ARCHIVE"
    SKIP = "SKIP"
    PERCENTAGE_ROUTER = "PERCENTAGE_ROUTER"
    COLLABORATOR_ROUTER = "COLLABORATOR_ROUTER"
    UNKNOWN = "_UNKNOWN_"


class PathwayVerdict(ReadEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    NEUTRAL = "neutral"
    UNKNOWN = "_UNKNOWN_"


class ReadOnlyDTO(BaseDTO):
    """A response model whose fields cannot be reassigned."""

    model_config: ClassVar["ConfigDict"] = {**BaseDTO.model_config, "frozen": True}


class PathwayDTO(ReadOnlyDTO):
    id: UUID
    name: Optional[str] = None
    source_stage_id: UUID
    destination_stage_id: UUID
    verdict: PathwayVerdict


class EmptySettingsDTO(ReadOnlyDTO):
    version: Literal[1]


class UnknownSettingsDTO(ReadOnlyDTO):
    values: Dict[str, Any]

    @model_serializer
    def serialize_settings(self) -> Dict[str, Any]:
        return self.values

    @dto_validator(mode="before")
    @classmethod
    def require_unfamiliar_version(cls, values: Any) -> Any:
        if isinstance(values, cls):
            return values
        if not isinstance(values, dict):
            raise ValueError("Expected settings with an unfamiliar version.")
        version = values.get("version")
        if type(version) is not int or version < 2:
            raise ValueError("Expected settings with an unfamiliar version.")
        return {"values": values}


class StageDTO(BaseDTO):
    id: UUID
    name: str


class StartStageDTO(StageDTO):
    stage_type: Literal[StageType.START]
    settings: Union[EmptySettingsDTO, UnknownSettingsDTO]


class AnnotationStageDTO(StageDTO):
    stage_type: Literal[StageType.ANNOTATION]
    settings: Union[EmptySettingsDTO, UnknownSettingsDTO]


class ReviewStageDTO(StageDTO):
    stage_type: Literal[StageType.REVIEW]
    settings: Union[EmptySettingsDTO, UnknownSettingsDTO]


class ExternalStageDTO(StageDTO):
    stage_type: Literal[StageType.EXTERNAL]
    settings: Union[EmptySettingsDTO, UnknownSettingsDTO]


class CompleteStageDTO(StageDTO):
    stage_type: Literal[StageType.COMPLETE]
    settings: Union[EmptySettingsDTO, UnknownSettingsDTO]


class ArchiveStageDTO(StageDTO):
    stage_type: Literal[StageType.ARCHIVE]
    settings: Union[EmptySettingsDTO, UnknownSettingsDTO]


class SkipStageDTO(StageDTO):
    stage_type: Literal[StageType.SKIP]
    settings: Union[EmptySettingsDTO, UnknownSettingsDTO]


class PercentageRouterSettingsV1DTO(EmptySettingsDTO):
    pathway_probabilities: Dict[UUID, float] = Field(alias="pathwayToPercentageMapping")


class PercentageRouterStageDTO(StageDTO):
    stage_type: Literal[StageType.PERCENTAGE_ROUTER]
    settings: Union[PercentageRouterSettingsV1DTO, UnknownSettingsDTO]


class CollaboratorRouterStageDTO(StageDTO):
    stage_type: Literal[StageType.COLLABORATOR_ROUTER]
    settings: Union[EmptySettingsDTO, UnknownSettingsDTO]


class UnknownStageDTO(StageDTO):
    stage_type: str
    settings: Dict[str, Any]

    @dto_validator(mode="before")
    @classmethod
    def require_unfamiliar_stage_type(cls, values: Any) -> Any:
        if isinstance(values, cls):
            return values
        stage_type = (values.get("stageType") or values.get("stage_type")) if isinstance(values, dict) else None
        if not isinstance(stage_type, str) or StageType(stage_type) is not StageType.UNKNOWN:
            raise ValueError("Expected an unfamiliar stage type.")
        return values


WorkflowStageDTO = Union[
    StartStageDTO,
    AnnotationStageDTO,
    ReviewStageDTO,
    ExternalStageDTO,
    CompleteStageDTO,
    ArchiveStageDTO,
    SkipStageDTO,
    PercentageRouterStageDTO,
    CollaboratorRouterStageDTO,
    UnknownStageDTO,
]


class WorkflowV3DTO(BaseDTO):
    id: UUID
    stages: Tuple[WorkflowStageDTO, ...]
    pathways: Tuple[PathwayDTO, ...]
