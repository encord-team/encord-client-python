"""Asynchronous project copying."""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union
from uuid import UUID

from pydantic import ValidationError

from encord.configs import Config
from encord.exceptions import EncordException, TimeOutError
from encord.http.v2.api_client import ApiClient
from encord.orm import project_copy as dto
from encord.utilities.hash_utilities import convert_to_uuid

if TYPE_CHECKING:
    from encord.project import Project

_MAX_REQUEST_WAIT_SECONDS = 60
_DEFAULT_PROJECT_WAIT_SECONDS = 60 * 60
_MIN_POLL_INTERVAL_SECONDS = 1


@dataclass(frozen=True)
class AllDatasets:
    """Attach all of the source project's existing datasets to the copy."""


@dataclass(frozen=True)
class SelectedDatasets:
    """Attach selected source datasets. An empty selection copies no data."""

    dataset_ids: Sequence[Union[str, UUID]]


@dataclass(frozen=True)
class ProjectCopyFile:
    """A data unit selected for copying."""

    dataset_id: Union[str, UUID]
    data_id: Union[str, UUID]


@dataclass(frozen=True)
class SelectedFiles:
    """Copy selected data units into a new dataset without duplicating their source files."""

    files: Sequence[ProjectCopyFile]
    dataset_title: Optional[str] = None


ProjectCopyDataSelection = Union[AllDatasets, SelectedDatasets, SelectedFiles]


class ProjectCopyStatus(str, Enum):
    """The status of a project copy."""

    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    UNKNOWN = "_UNKNOWN_"

    @classmethod
    def _missing_(cls, value: Any) -> "ProjectCopyStatus":
        return cls.UNKNOWN


@dataclass(frozen=True)
class ProjectCopyResult:
    """A copy's status and result. ``raw_status`` is set for unrecognized statuses."""

    job_id: UUID
    status: ProjectCopyStatus
    project_id: Optional[UUID] = None
    error: Optional[str] = None
    raw_status: Optional[str] = None


class ProjectCopyFailedError(EncordException):
    """The copy failed; ``error`` contains the reason."""

    def __init__(self, message: str, *, job_id: Optional[UUID] = None, error: Optional[str] = None) -> None:
        super().__init__(message)
        self.job_id = job_id
        self.error = error


class ProjectCopyTimeoutError(TimeOutError):
    """The wait expired, but the copy continues running."""

    def __init__(self, message: str, *, job_id: Optional[UUID] = None) -> None:
        super().__init__(message)
        self.job_id = job_id


class ProjectCopyWaitError(EncordException):
    """Waiting stopped before the copy's outcome was known; use ``job_id`` to resume."""

    def __init__(self, message: str, *, job_id: Optional[UUID] = None) -> None:
        super().__init__(message)
        self.job_id = job_id


class ProjectCopyLoadError(EncordException):
    """The copy succeeded, but loading the project identified by ``project_id`` failed."""

    def __init__(self, message: str, *, job_id: Optional[UUID] = None, project_id: Optional[UUID] = None) -> None:
        super().__init__(message)
        self.job_id = job_id
        self.project_id = project_id


@dataclass(frozen=True)
class ProjectCopyJob:
    """A background project copy, identified by ``job_id``.

    ``project_id`` is set when starting a copy and is None on resumed handles.
    For resumed jobs, read the project ID from the result of ``get_status()``.
    """

    job_id: UUID
    _api_client: ApiClient = field(repr=False, compare=False)
    _config: Config = field(repr=False, compare=False)
    project_id: Optional[UUID] = None

    def get_status(self, timeout_seconds: int = 0) -> ProjectCopyResult:
        """Return the copy's current status.

        A positive timeout waits until the status leaves PENDING or the wait expires.
        An expired wait returns PENDING without canceling the copy.

        Args:
            timeout_seconds: Maximum wait in seconds. Defaults to 0, which checks once without waiting.

        Raises:
            EncordException: The status response could not be read.
        """
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        response = self._poll(timeout_seconds)
        if isinstance(response, dto.ProjectCopyFailedDTO):
            return ProjectCopyResult(self.job_id, ProjectCopyStatus.FAILED, error=response.error)
        if isinstance(response, dto.ProjectCopyUnknownDTO):
            return ProjectCopyResult(
                self.job_id,
                ProjectCopyStatus.UNKNOWN,
                response.project_uuid,
                response.error,
                raw_status=response.status,
            )
        return ProjectCopyResult(self.job_id, ProjectCopyStatus(response.status), response.project_uuid)

    def wait_for_project(self, timeout_seconds: Optional[int] = _DEFAULT_PROJECT_WAIT_SECONDS) -> "Project":
        """Wait for the copy to finish and return the copied project.

        Args:
            timeout_seconds: Maximum wait in seconds, or None to wait indefinitely. Defaults to one hour.

        Raises:
            ProjectCopyFailedError: The copy failed.
            ProjectCopyTimeoutError: The wait expired; the copy continues running.
            ProjectCopyWaitError: Reading the status failed or the status is unrecognized.
            ProjectCopyLoadError: The copy succeeded but its project could not be loaded.
        """
        if timeout_seconds is not None and timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        try:
            response = self._poll(timeout_seconds)
        except EncordException as error:
            raise ProjectCopyWaitError(
                f"Could not read the status of project copy job '{self.job_id}'.", job_id=self.job_id
            ) from error
        if isinstance(response, dto.ProjectCopyPendingDTO):
            raise ProjectCopyTimeoutError(
                f"Project copy job '{self.job_id}' is still running; waiting again will pick it up.", job_id=self.job_id
            )
        if isinstance(response, dto.ProjectCopyFailedDTO):
            raise ProjectCopyFailedError(
                f"Project copy job '{self.job_id}' failed: {response.error}", job_id=self.job_id, error=response.error
            )
        if not isinstance(response, dto.ProjectCopyDoneDTO):
            raise ProjectCopyWaitError(
                f"Project copy job '{self.job_id}' returned unrecognized status '{response.status}'; "
                "this SDK cannot determine whether the copy succeeded.",
                job_id=self.job_id,
            )
        # Project exposes copy jobs, so defer this import to avoid a module cycle.
        from encord.project import _load_project

        try:
            return _load_project(self._api_client, self._config, response.project_uuid)
        except (EncordException, ValidationError) as error:
            raise ProjectCopyLoadError(
                f"Project copy job '{self.job_id}' succeeded, but project '{response.project_uuid}' could not be loaded.",
                job_id=self.job_id,
                project_id=response.project_uuid,
            ) from error

    def _poll(self, timeout_seconds: Optional[int]) -> dto.ProjectCopyOutcomeDTO:
        """Wait until the status leaves pending or the wait expires."""
        deadline = math.inf if timeout_seconds is None else time.monotonic() + timeout_seconds

        while True:
            request_start = time.monotonic()
            request_wait = math.floor(
                min(
                    max(0.0, deadline - request_start),
                    _MAX_REQUEST_WAIT_SECONDS,
                    max(0, self._api_client.requests_settings.read_timeout - 1),
                )
            )
            try:
                response = self._api_client.get(
                    f"projects/copy-jobs/{self.job_id}",
                    params=dto.ProjectCopyResultParams(timeout_seconds=request_wait),
                    result_type=dto.ProjectCopyResultDTO,
                ).root
            except ValidationError as error:
                raise EncordException(
                    f"The platform returned an invalid status response for project copy job '{self.job_id}'."
                ) from error
            now = time.monotonic()
            if not isinstance(response, dto.ProjectCopyPendingDTO) or now >= deadline:
                return response
            delay = min(deadline - now, max(0.0, _MIN_POLL_INTERVAL_SECONDS - (now - request_start)))
            if delay > 0:
                time.sleep(delay)
            if time.monotonic() >= deadline:
                return response


def _start_project_copy(
    api_client: ApiClient,
    config: Config,
    project_id: UUID,
    *,
    data: ProjectCopyDataSelection,
    title: Optional[str],
    description: Optional[str],
    copy_labels: bool,
    copy_collaborators: bool,
) -> ProjectCopyJob:
    selection: Union[dto.CopyAllDatasetsDTO, dto.CopyDatasetsDTO, dto.CopyFilesDTO]
    if isinstance(data, AllDatasets):
        selection = dto.CopyAllDatasetsDTO()
    elif isinstance(data, SelectedDatasets):
        selection = dto.CopyDatasetsDTO(dataset_uuids=[convert_to_uuid(value) for value in data.dataset_ids])
    elif isinstance(data, SelectedFiles):
        selection = dto.CopyFilesDTO(
            files=[
                dto.CopyFileDTO(dataset_uuid=convert_to_uuid(item.dataset_id), data_uuid=convert_to_uuid(item.data_id))
                for item in data.files
            ],
            dataset_title=data.dataset_title,
        )
    else:
        raise TypeError("data must be AllDatasets, SelectedDatasets or SelectedFiles")
    started = api_client.post(
        f"projects/{project_id}/copy-jobs",
        params=None,
        payload=dto.StartProjectCopyPayload(
            title=title,
            description=description,
            data=selection,
            copy_labels=copy_labels,
            copy_collaborators=copy_collaborators,
        ),
        result_type=dto.ProjectCopyStartedDTO,
        allow_retries=False,
    )
    return ProjectCopyJob(started.job_uuid, api_client, config, started.project_uuid)
