"""Request and response models for project copy jobs."""

from typing import List, Literal, Optional, Union
from uuid import UUID

from pydantic import RootModel, field_validator

from encord.orm.base_dto import BaseDTO


class CopyAllDatasetsDTO(BaseDTO):
    type: Literal["allDatasets"] = "allDatasets"


class CopyDatasetsDTO(BaseDTO):
    type: Literal["datasets"] = "datasets"
    dataset_uuids: List[UUID]


class CopyFileDTO(BaseDTO):
    dataset_uuid: UUID
    data_uuid: UUID


class CopyFilesDTO(BaseDTO):
    type: Literal["files"] = "files"
    files: List[CopyFileDTO]
    dataset_title: Optional[str] = None


class StartProjectCopyPayload(BaseDTO):
    title: Optional[str] = None
    description: Optional[str] = None
    data: Union[CopyAllDatasetsDTO, CopyDatasetsDTO, CopyFilesDTO]
    copy_labels: bool = False
    copy_collaborators: bool = False


class ProjectCopyStartedDTO(BaseDTO):
    job_uuid: UUID
    project_uuid: UUID


class ProjectCopyPendingDTO(BaseDTO):
    status: Literal["pending"]
    project_uuid: UUID


class ProjectCopyDoneDTO(BaseDTO):
    status: Literal["done"]
    project_uuid: UUID


class ProjectCopyFailedDTO(BaseDTO):
    status: Literal["failed"]
    error: str


class ProjectCopyUnknownDTO(BaseDTO):
    status: str
    project_uuid: Optional[UUID] = None
    error: Optional[str] = None

    @field_validator("status")
    @classmethod
    def require_unfamiliar_status(cls, value: str) -> str:
        if value in ("pending", "done", "failed"):
            raise ValueError("Expected an unfamiliar copy status.")
        return value


ProjectCopyOutcomeDTO = Union[ProjectCopyPendingDTO, ProjectCopyDoneDTO, ProjectCopyFailedDTO, ProjectCopyUnknownDTO]


class ProjectCopyResultDTO(RootModel[ProjectCopyOutcomeDTO]):
    pass


class ProjectCopyResultParams(BaseDTO):
    timeout_seconds: int
