"""Connections in a workflow graph."""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID

from encord.orm.workflow_v3 import PathwayVerdict


@dataclass(frozen=True)
class Pathway:
    """An outgoing connection; names may be absent or shared by several pathways."""

    id: UUID
    source_stage_id: UUID
    destination_stage_id: UUID
    verdict: PathwayVerdict
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Export using Python field names, string UUIDs and enum values."""
        return {
            "id": str(self.id),
            "name": self.name,
            "source_stage_id": str(self.source_stage_id),
            "destination_stage_id": str(self.destination_stage_id),
            "verdict": self.verdict.value,
        }
