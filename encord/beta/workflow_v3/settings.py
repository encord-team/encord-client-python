"""Read-only public configuration, independent of API response models."""

from copy import deepcopy
from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Literal, Mapping, Optional
from uuid import UUID


def _export_value(value: Any) -> Any:
    if isinstance(value, Settings):
        return value.to_dict()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _export_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_export_value(item) for item in value]
    return deepcopy(value)


@dataclass(frozen=True)
class Settings:
    """Read-only configuration with detached, JSON-safe export using Python field names."""

    def to_dict(self) -> Dict[str, Any]:
        return {item.name: _export_value(getattr(self, item.name)) for item in fields(self)}


@dataclass(frozen=True)
class StageSettings(Settings):
    """Read-only public configuration for a workflow stage."""


@dataclass(frozen=True)
class StartStageSettingsV1(StageSettings):
    """Start has no public configuration fields."""

    version: Literal[1] = field(default=1, init=False)


@dataclass(frozen=True)
class AnnotationStageSettingsV1(StageSettings):
    """Annotation stages have no public configuration fields."""

    version: Literal[1] = field(default=1, init=False)


@dataclass(frozen=True)
class ReviewStageSettingsV1(StageSettings):
    """Review stages have no public configuration fields."""

    version: Literal[1] = field(default=1, init=False)


@dataclass(frozen=True)
class ExternalStageSettingsV1(StageSettings):
    """External stages have no public configuration fields."""

    version: Literal[1] = field(default=1, init=False)


@dataclass(frozen=True)
class CompleteStageSettingsV1(StageSettings):
    """Complete terminals have no public configuration fields."""

    version: Literal[1] = field(default=1, init=False)


@dataclass(frozen=True)
class ArchiveStageSettingsV1(StageSettings):
    """Archive terminals have no public configuration fields."""

    version: Literal[1] = field(default=1, init=False)


@dataclass(frozen=True)
class SkipStageSettingsV1(StageSettings):
    """Skip terminals have no public configuration fields."""

    version: Literal[1] = field(default=1, init=False)


@dataclass(frozen=True)
class UnknownStageSettings(StageSettings):
    """Unfamiliar settings; to_dict returns a detached copy with original keys."""

    _values: Dict[str, Any] = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_values", deepcopy(self._values))

    def to_dict(self) -> Dict[str, Any]:
        return deepcopy(self._values)

    @property
    def version(self) -> Optional[int]:
        """Settings contract version, if supplied by an unfamiliar stage."""
        return self._values.get("version")


@dataclass(frozen=True, init=False)
class PercentageRouterStageSettingsV1(StageSettings):
    """Probabilities by pathway UUID, expressed as fractions summing to one."""

    version: Literal[1] = field(default=1, init=False)
    _probabilities: Dict[UUID, float] = field(repr=False)

    def __init__(self, pathway_probabilities: Mapping[UUID, float]) -> None:
        object.__setattr__(self, "_probabilities", dict(pathway_probabilities))

    @property
    def pathway_probabilities(self) -> Mapping[UUID, float]:
        """Read-only probabilities for this router's outgoing pathways."""
        return MappingProxyType(self._probabilities)

    def to_dict(self) -> Dict[str, Any]:
        return {"version": self.version, "pathway_probabilities": _export_value(self.pathway_probabilities)}


@dataclass(frozen=True)
class CollaboratorRouterStageSettingsV1(StageSettings):
    """Collaborator routers have no public configuration fields."""

    version: Literal[1] = field(default=1, init=False)
