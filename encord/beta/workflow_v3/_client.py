"""Client context shared by a workflow and its stages."""

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from encord.http.v2.api_client import ApiClient


@dataclass(frozen=True)
class WorkflowClient:
    api_client: "ApiClient"
    project_id: UUID
