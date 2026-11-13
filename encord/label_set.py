"""Label sets capture the labels of a project branch into frozen versions.

A label set names a project branch as its source and, optionally, a selection of that branch's labels. Creating a version
captures every selected label at its current revision into a new version. A version never changes once it
is READY, so it can be exported again later or compared with another version.

Entry points are on :class:`encord.user_client.EncordUserClient`: ``create_label_set``, ``get_label_set``
and ``list_label_sets``.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable, Iterator, List, Optional, Sequence, TypeVar, Union, cast
from uuid import UUID

from pydantic import ValidationError

from encord.common.polling import PollingSchedule, poll_job
from encord.exceptions import EncordException
from encord.http.v2.api_client import ApiClient
from encord.objects.ontology_structure import OntologyStructure
from encord.orm.label_set import (
    CreateLabelSetPayload,
    CreateVersionExportPayload,
    CreateVersionPayload,
    ExportFormat,
    LabelSelection,
    LabelSetJob,
    LabelSetJobPending,
    LabelSetOrigin,
    LabelSetPageParams,
    LabelSetVersionMember,
    LabelSetVersionStatus,
    ListLabelSetsParams,
    ProjectSource,
    SetLabelSelectionPayload,
    StoredCapturedSource,
    StoredSource,
    UpdateLabelSetPayload,
    VersionExportJob,
    VersionExportJobResponse,
    VersionJob,
    VersionJobResponse,
    VersionOntology,
)
from encord.orm.label_set import LabelSet as OrmLabelSet
from encord.orm.label_set import LabelSetVersion as OrmLabelSetVersion

JobT = TypeVar("JobT", VersionJob, VersionExportJob)

# A version job finishes in seconds to a couple of minutes; an export of a large version can run for longer.
VERSION_JOB_POLLING = PollingSchedule(initial_seconds=1.0, max_seconds=5.0)
EXPORT_JOB_POLLING = PollingSchedule(initial_seconds=2.0, max_seconds=15.0)


def _job_state(get_job: Callable[[], JobT], timeout_seconds: float, schedule: PollingSchedule) -> JobT:
    """The job's state now, or after waiting up to ``timeout_seconds`` for it to leave pending.

    A job still pending when the wait ends is returned as pending. The caller holds the job id and can read it
    again. A ``timeout_seconds`` of zero or less reads the state once.
    """

    def read_job() -> JobT:
        # The job envelopes are root models, which the API client validates without wrapping the error.
        try:
            return get_job()
        except ValidationError as e:
            raise EncordException(message=f"The platform returned a job state this SDK cannot read: {e}") from e

    job = poll_job(
        read_job, lambda job: isinstance(job, LabelSetJobPending), time.monotonic() + timeout_seconds, schedule
    )
    return job if job is not None else cast(JobT, LabelSetJobPending())


class LabelSet:
    """A label set: a project branch, which of its labels to capture, and the versions created from them.

    Obtain one with :meth:`encord.user_client.EncordUserClient.get_label_set`,
    :meth:`encord.user_client.EncordUserClient.list_label_sets` or
    :meth:`encord.user_client.EncordUserClient.create_label_set`.
    """

    def __init__(self, client: ApiClient, orm_label_set: OrmLabelSet):
        self._client = client
        self._instance = orm_label_set

    @property
    def id(self) -> UUID:
        """Get the unique identifier of the label set.

        Returns:
            UUID: The label set ID.
        """
        return self._instance.id

    @property
    def name(self) -> str:
        """Get the name of the label set.

        Returns:
            str: The name.
        """
        return self._instance.name

    @property
    def description(self) -> str:
        """Get the description of the label set.

        Returns:
            str: The description, empty when none was given.
        """
        return self._instance.description

    @property
    def origin(self) -> LabelSetOrigin:
        """Get where the set's labels come from.

        Returns:
            LabelSetOrigin: ``WORKFLOW`` for labels made in the project, ``IMPORT`` for labels written to the branch
            from outside, such as model predictions.
        """
        return self._instance.origin

    @property
    def sources(self) -> List[StoredSource]:
        """Get the project branches that feed the set, each with its selection.

        A listed source carries its ID, project and branch. To read its selection, call :meth:`refetch_data`
        on the label set and read ``sources`` again.

        Returns:
            List[StoredSource]: One :class:`encord.orm.label_set.StoredProjectSource` today: the project, the branch a
            version captures, and its ``label_selection`` (:class:`encord.orm.label_set.AllSelection` when a
            version captures every label on the branch). An :class:`encord.orm.label_set.UnknownSource` is a kind
            of source this SDK version does not recognize.

        Example:
            >>> source = label_set.sources[0]
            >>> if isinstance(source, StoredProjectSource):
            ...     print(source.project_id, source.branch_name, source.label_selection)
        """
        return self._instance.sources

    @property
    def created_by_email(self) -> str:
        """Get the email of the user who created the set.

        Returns:
            str: The creator's email.
        """
        return self._instance.created_by_email

    @property
    def created_at(self) -> datetime:
        """Get when the set was created.

        Returns:
            datetime: The creation time.
        """
        return self._instance.created_at

    def refetch_data(self) -> None:
        """Read the label set again from the platform, including each source's selection."""
        self._instance = LabelSet._fetch(self._client, self.id)

    @staticmethod
    def _fetch(api_client: ApiClient, label_set_id: UUID) -> OrmLabelSet:
        return api_client.get(f"label-sets/{label_set_id}", params=None, result_type=OrmLabelSet)

    @staticmethod
    def _get_label_set(api_client: ApiClient, label_set_id: UUID) -> LabelSet:
        return LabelSet(api_client, LabelSet._fetch(api_client, label_set_id))

    @staticmethod
    def _list_label_sets(
        api_client: ApiClient, project_id: Optional[UUID], page_size: Optional[int]
    ) -> Iterator[LabelSet]:
        params = ListLabelSetsParams(project_id=project_id, page_size=page_size)
        for item in api_client.get_paged_iterator("label-sets", params=params, result_type=OrmLabelSet):
            yield LabelSet(api_client, item)

    @staticmethod
    def _create_label_set(
        api_client: ApiClient,
        name: str,
        sources: Sequence[ProjectSource],
        description: str,
        origin: LabelSetOrigin,
    ) -> LabelSet:
        payload = CreateLabelSetPayload(sources=list(sources), name=name, description=description, origin=origin)
        created = api_client.post(
            "label-sets",
            params=None,
            payload=payload,
            result_type=OrmLabelSet,
            # A retry after the set was created would create a second set with the same name.
            allow_retries=False,
        )
        return LabelSet(api_client, created)

    def update(self, *, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """Change the name or the description. An argument left as ``None`` is unchanged.

        Args:
            name: The new name.
            description: The new description. Pass ``""`` to clear it.

        Raises:
            :class:`encord.exceptions.AuthorisationError`: You cannot manage the set.
        """
        if name is None and description is None:
            return
        self._patch(UpdateLabelSetPayload(name=name, description=description))

    def set_label_selection(self, source_id: Union[str, UUID], selection: LabelSelection) -> None:
        """Replace which labels a version captures from one source.

        Example:
            >>> complete = project.workflow.get_stage(name="Complete")
            >>> source = label_set.sources[0]
            >>> if isinstance(source, StoredProjectSource):
            ...     label_set.set_label_selection(source.id, WorkflowStageSelection(workflow_stage_ids=[complete.uuid]))
            ...     label_set.set_label_selection(source.id, AllSelection())  # back to every label on the branch

        Args:
            source_id: The source under this label set. Available on listed sources too.
            selection: A :class:`encord.orm.label_set.WorkflowStageSelection` (on the ``main`` branch only), or
                :class:`encord.orm.label_set.AllSelection` so that the next version captures every label on the
                branch.

        Raises:
            :class:`encord.exceptions.AuthorisationError`: You cannot manage the set.
            :class:`encord.exceptions.ResourceNotFoundError`: The source does not belong to this label set.
            :class:`encord.exceptions.EncordException`: A stage selection was given for a branch other than ``main``.
            ValueError: ``source_id`` is a badly formed UUID.
        """
        if isinstance(source_id, str):
            source_id = UUID(source_id)
        self._client.patch(
            f"label-sets/{self.id}/sources/{source_id}",
            params=None,
            payload=SetLabelSelectionPayload(label_selection=selection),
            result_type=None,
        )
        self.refetch_data()

    def _patch(self, payload: UpdateLabelSetPayload) -> None:
        # The route returns no body, so the set is read again to reflect the change.
        self._client.patch(f"label-sets/{self.id}", params=None, payload=payload, result_type=None)
        self.refetch_data()

    def list_versions(self, *, page_size: Optional[int] = None) -> Iterator[LabelSetVersion]:
        """List the versions of the set, newest first.

        Args:
            page_size: Number of versions per page. Default 100, maximum 100.

        Returns:
            Iterator[LabelSetVersion]: The versions.
        """
        params = LabelSetPageParams(page_size=page_size)
        for item in self._client.get_paged_iterator(
            f"label-sets/{self.id}/versions", params=params, result_type=OrmLabelSetVersion
        ):
            yield LabelSetVersion(self._client, item)

    def get_version(self, version_id: Union[str, UUID]) -> LabelSetVersion:
        """Get one version of the set.

        Args:
            version_id: The version.

        Returns:
            LabelSetVersion: The version.

        Raises:
            ValueError: ``version_id`` is a badly formed UUID.
            :class:`encord.exceptions.ResourceNotFoundError`: The version does not exist under this set, or you
                cannot read it.
        """
        if isinstance(version_id, str):
            version_id = UUID(version_id)
        item = self._client.get(
            f"label-sets/{self.id}/versions/{version_id}", params=None, result_type=OrmLabelSetVersion
        )
        return LabelSetVersion(self._client, item)

    def create_version_job(self, name: Optional[str] = None) -> UUID:
        """Queue a new version of the set's current selection, and return without waiting.

        Read the job with :meth:`get_version_job`; once it is done, the version is available through
        :meth:`get_version`.

        Example:
            >>> job_id = label_set.create_version_job("v1")
            >>> job = label_set.get_version_job(job_id, timeout_seconds=600)
            >>> if isinstance(job, VersionJobDone):
            ...     version = label_set.get_version(job.version_id)

        Args:
            name: A label for the version, shown with its number. ``None`` means the number alone.

        Returns:
            UUID: The job.

        Raises:
            :class:`encord.exceptions.AuthorisationError`: You cannot manage the set.
        """
        return self._client.post(
            f"label-sets/{self.id}/versions",
            params=None,
            payload=CreateVersionPayload(name=name),
            result_type=LabelSetJob,
            # A retry after the job was queued would create a second version.
            allow_retries=False,
        ).job_id

    def get_version_job(self, job_id: Union[str, UUID], *, timeout_seconds: float = 0) -> VersionJob:
        """Get the state of a version job, waiting up to ``timeout_seconds`` for it to finish.

        Args:
            job_id: The job, as returned by :meth:`create_version_job`.
            timeout_seconds: How long to wait while the job is pending, polling with backoff. ``0`` reads the state
                once and returns it. The job is never cancelled; a pending result after the wait means it is still
                running and can be read again.

        Returns:
            VersionJob: One of :class:`encord.orm.label_set.LabelSetJobPending`,
            :class:`encord.orm.label_set.VersionJobDone` with the version it created,
            :class:`encord.orm.label_set.VersionJobFailed` with the reason (no version was created), or
            :class:`encord.orm.label_set.LabelSetJobUnknown` for a state this SDK version does not recognize.

        Raises:
            ValueError: ``job_id`` is a badly formed UUID.
            :class:`encord.exceptions.ResourceNotFoundError`: The job does not exist under this set, or you cannot
                read it.
            :class:`encord.exceptions.EncordException`: The platform returned a job state this SDK cannot read.
        """
        if isinstance(job_id, str):
            job_id = UUID(job_id)
        path = f"label-sets/{self.id}/versions/jobs/{job_id}"
        return _job_state(
            lambda: self._client.get(path, params=None, result_type=VersionJobResponse).root,
            timeout_seconds,
            VERSION_JOB_POLLING,
        )


class LabelSetVersion:
    """A version of a label set: a frozen record of the labels captured when it was created.

    Obtain one with :meth:`LabelSet.get_version` or :meth:`LabelSet.list_versions`. A new version is queued with
    :meth:`LabelSet.create_version_job`.
    """

    def __init__(self, client: ApiClient, orm_version: OrmLabelSetVersion):
        self._client = client
        self._instance = orm_version

    @property
    def id(self) -> UUID:
        """Get the unique identifier of the version.

        Returns:
            UUID: The version ID.
        """
        return self._instance.id

    @property
    def label_set_id(self) -> UUID:
        """Get the label set the version belongs to.

        Returns:
            UUID: The label set ID.
        """
        return self._instance.label_set_id

    @property
    def sources(self) -> List[StoredCapturedSource]:
        """Get what the version captured.

        Returns:
            List[StoredCapturedSource]: One :class:`encord.orm.label_set.CapturedSource` today: the project branch
            the version captured, with the ontology and revision its labels were made against when it was created. An
            :class:`encord.orm.label_set.UnknownSource` is a kind of source this SDK version does not recognize.

        Example:
            >>> source = version.sources[0]
            >>> if isinstance(source, CapturedSource):
            ...     print(source.ontology_id, source.ontology_version_id)
        """
        return self._instance.sources

    @property
    def version_number(self) -> int:
        """Get the position of the version in its set, from 1.

        Returns:
            int: The version number.
        """
        return self._instance.version_number

    @property
    def name(self) -> str:
        """Get the name of the version.

        Returns:
            str: The name.
        """
        return self._instance.name

    @property
    def status(self) -> LabelSetVersionStatus:
        """Get the lifecycle of the version.

        Returns:
            LabelSetVersionStatus: ``BUILDING``, ``READY`` or ``FAILED``.
        """
        return self._instance.status

    @property
    def created_by_email(self) -> str:
        """Get the email of the user who created the version.

        Returns:
            str: The creator's email.
        """
        return self._instance.created_by_email

    @property
    def capture_started_at(self) -> datetime:
        """Get when the capture started.

        Returns:
            datetime: The start time.
        """
        return self._instance.capture_started_at

    @property
    def capture_finished_at(self) -> Optional[datetime]:
        """Get when the capture finished.

        Returns:
            Optional[datetime]: The finish time, or ``None`` while the version is building.
        """
        return self._instance.capture_finished_at

    @property
    def label_count(self) -> Optional[int]:
        """Get how many labels the version holds.

        Returns:
            Optional[int]: The count, or ``None`` until the version is READY.
        """
        return self._instance.label_count

    def refetch_data(self) -> None:
        """Read the version again from the platform."""
        self._instance = self._client.get(
            f"label-sets/{self.label_set_id}/versions/{self.id}", params=None, result_type=OrmLabelSetVersion
        )

    def get_ontology(self) -> OntologyStructure:
        """Get the ontology the version's labels were made against, as it was when the version was created.

        Compare this rather than the ids on :attr:`sources`: editing a shared class changes the definition without
        a new revision, so two versions can share a revision id and still differ.

        Returns:
            OntologyStructure: The frozen ontology.
        """
        ontology = self._client.get(
            f"label-sets/{self.label_set_id}/versions/{self.id}/ontology", params=None, result_type=VersionOntology
        )
        return OntologyStructure.from_dict(ontology.editor)

    def list_members(self, *, page_size: Optional[int] = None) -> Iterator[LabelSetVersionMember]:
        """List the labels the version holds, each at the revision captured, in label ID order.

        Args:
            page_size: Number of labels per page. Default 100, maximum 100.

        Returns:
            Iterator[LabelSetVersionMember]: The labels, with the storage item each one was on.
        """
        params = LabelSetPageParams(page_size=page_size)
        return self._client.get_paged_iterator(
            f"label-sets/{self.label_set_id}/versions/{self.id}/members",
            params=params,
            result_type=LabelSetVersionMember,
        )

    def create_export_job(self, format: ExportFormat = ExportFormat.JSON) -> UUID:
        """Queue an export of the labels the version holds, and return without waiting.

        Read the job with :meth:`get_export_job`; once it is done, it carries a link to the archive.

        Example:
            >>> job_id = version.create_export_job(ExportFormat.COCO)
            >>> job = version.get_export_job(job_id, timeout_seconds=600)
            >>> if isinstance(job, VersionExportJobDone):
            ...     archive = requests.get(job.signed_url).content

        Args:
            format: Format of the export.

        Returns:
            UUID: The job.

        Raises:
            :class:`encord.exceptions.AuthorisationError`: You cannot manage the captured project.
        """
        return self._client.post(
            f"label-sets/{self.label_set_id}/versions/{self.id}/exports",
            params=None,
            payload=CreateVersionExportPayload(format=format),
            result_type=LabelSetJob,
            # A retry after the job was queued would run a second export.
            allow_retries=False,
        ).job_id

    def get_export_job(self, job_id: Union[str, UUID], *, timeout_seconds: float = 0) -> VersionExportJob:
        """Get the state of an export job, waiting up to ``timeout_seconds`` for it to finish.

        Args:
            job_id: The job, as returned by :meth:`create_export_job`.
            timeout_seconds: How long to wait while the job is pending, polling with backoff. ``0`` reads the state
                once and returns it. The job is never cancelled; a pending result after the wait means it is still
                running and can be read again.

        Returns:
            VersionExportJob: One of :class:`encord.orm.label_set.LabelSetJobPending`,
            :class:`encord.orm.label_set.VersionExportJobDone` with a link to the archive, valid for seven days
            and renewed on each read, :class:`encord.orm.label_set.VersionExportJobFailed`, or
            :class:`encord.orm.label_set.LabelSetJobUnknown` for a state this SDK version does not recognize.

        Raises:
            ValueError: ``job_id`` is a badly formed UUID.
            :class:`encord.exceptions.ResourceNotFoundError`: The job does not exist under this version, or you
                cannot read it.
            :class:`encord.exceptions.EncordException`: The platform returned a job state this SDK cannot read.
        """
        if isinstance(job_id, str):
            job_id = UUID(job_id)
        path = f"label-sets/{self.label_set_id}/versions/{self.id}/exports/jobs/{job_id}"
        return _job_state(
            lambda: self._client.get(path, params=None, result_type=VersionExportJobResponse).root,
            timeout_seconds,
            EXPORT_JOB_POLLING,
        )
