"""Wire shapes of the label set routes under ``/v2/public/label-sets``.

Identifiers are ``*_id`` in Python and ``*Uuid`` on the wire.
"""

from __future__ import annotations

from datetime import datetime
from enum import auto
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import SerializerFunctionWrapHandler, model_serializer

from encord.exceptions import EncordException
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO, BaseDTOWithExtra, Field, RootModelDTO, dto_validator


def _wire(name: str, **kwargs: Any) -> Any:
    """A field whose wire name differs from its Python name. Constructors take the Python name.

    ``Field(alias=...)`` is not used because the type checker then demands the wire name in every constructor call;
    splitting the alias into its validation and serialization halves keeps the Python name as the constructor argument.
    """
    return Field(validation_alias=name, serialization_alias=name, **kwargs)


def _uses_a_filter_other_than_stages(selection: Any) -> bool:
    """Whether a stored selection sets a filter this SDK does not expose: a data title search or a labeling status."""
    return isinstance(selection, dict) and (
        bool(selection.get("dataTitleSearch")) or selection.get("filterLabelingStatus") is not None
    )


class LabelSetOrigin(CamelStrEnum):
    """Where the labels of a label set come from.

    **Values:**

    - **WORKFLOW:** Labels made in the project's own workflow.
    - **IMPORT:** Labels written to the branch from outside the project, such as model predictions. An imported label
      set has no scheduled versions.
    - **UNKNOWN:** An origin this SDK version does not recognize.
    """

    WORKFLOW = auto()
    IMPORT = auto()

    UNKNOWN = "_UNKNOWN_"

    @classmethod
    def _missing_(cls, value: Any) -> LabelSetOrigin:
        """Return UNKNOWN for any origin added to the platform after this SDK version."""
        return cls.UNKNOWN


class LabelSetVersionStatus(CamelStrEnum):
    """Lifecycle of a label set version.

    **Values:**

    - **BUILDING:** The version is being captured.
    - **READY:** The version holds its labels and can be exported.
    - **FAILED:** The capture failed; the version holds no labels.
    - **UNKNOWN:** A status this SDK version does not recognize.
    """

    BUILDING = auto()
    READY = auto()
    FAILED = auto()

    UNKNOWN = "_UNKNOWN_"

    @classmethod
    def _missing_(cls, value: Any) -> LabelSetVersionStatus:
        """Return UNKNOWN for any status added to the platform after this SDK version."""
        return cls.UNKNOWN


class LabelSetJobStatus(CamelStrEnum):
    """Status of a label set job: creating a version or exporting one.

    **Values:**

    - **PENDING:** The job is queued or running.
    - **DONE:** The job finished and its result is available.
    - **FAILED:** The job failed.
    - **UNKNOWN:** A status this SDK version does not recognize.
    """

    PENDING = auto()
    DONE = auto()
    FAILED = auto()

    UNKNOWN = "_UNKNOWN_"

    @classmethod
    def _missing_(cls, value: Any) -> LabelSetJobStatus:
        """Return UNKNOWN for any status added to the platform after this SDK version."""
        return cls.UNKNOWN


class ExportFormat(CamelStrEnum):
    """Format of a label set version export.

    **Values:**

    - **JSON:** Encord's label JSON, one file per label row.
    - **COCO:** COCO format.
    """

    JSON = auto()
    COCO = auto()


class WorkflowStageSelection(BaseDTO):
    """A selection of the labels of the data units whose workflow task is at one of the listed stages.

    The stages are read when a version is created, so each version captures the tasks at those stages at that time.
    Workflow tasks exist on the ``main`` branch only, so the platform refuses this selection on any other branch.

    Example:
        >>> complete = project.workflow.get_stage(name="Complete")
        >>> selection = WorkflowStageSelection(workflow_stage_ids=[complete.uuid])
        >>> source = ProjectSource(project_id=project_id, label_selection=selection)

    Args:
        workflow_stage_ids: The stages whose tasks a version captures. An empty list captures every label on the
            branch.
    """

    tag: Literal["FILTERED"] = "FILTERED"
    workflow_stage_ids: List[UUID] = _wire("filterGraphNodeUuid")

    @dto_validator(mode="before")
    @classmethod
    def require_stage_filter_only(cls, values: Any) -> Any:
        # The platform stores filters this SDK does not set. A selection that uses one is not this shape.
        if _uses_a_filter_other_than_stages(values):
            raise ValueError("Expected a selection that filters by workflow stage only.")
        return values

    @model_serializer(mode="wrap")
    def _with_the_other_filters_unset(self, handler: SerializerFunctionWrapHandler) -> Dict[str, Any]:
        # The platform requires every filter, so the ones this SDK does not set are sent as unset.
        return {**handler(self), "dataTitleSearch": "", "filterLabelingStatus": None}


class AllSelection(BaseDTO):
    """Every label on the branch. The explicit form of no selection; a selection is never ``None``.

    Example:
        >>> label_set.set_label_selection(source.id, AllSelection())
    """

    tag: Literal["ALL"] = "ALL"


class UnknownSelection(BaseDTOWithExtra):
    """A selection this SDK version cannot set, kept as the platform sent it.

    The selection was set through the platform's web app or its API with a shape this SDK does not expose, such as
    a list of data units or a data title filter.

    Args:
        tag: The shape's name. The other fields are available as attributes.
    """

    tag: str

    @dto_validator(mode="before")
    @classmethod
    def require_unfamiliar_selection(cls, values: Any) -> Any:
        # A shape the SDK knows must parse as that shape, or fail if its body is malformed, rather than pass here.
        if isinstance(values, dict) and (
            values.get("tag") == "ALL"
            or (values.get("tag") == "FILTERED" and not _uses_a_filter_other_than_stages(values))
        ):
            raise ValueError("Expected a selection this SDK cannot set.")
        return values


LabelSelection = Union[AllSelection, WorkflowStageSelection]
"""A selection the SDK can set."""

StoredLabelSelection = Union[AllSelection, WorkflowStageSelection, UnknownSelection]
"""A selection as the platform returns it, which may be a shape this SDK version cannot set."""


class ProjectSource(BaseDTO):
    """A project branch that feeds a label set, and which of its labels a version captures.

    Args:
        project_id: The project.
        branch_name: The label branch a version captures.
        label_selection: Which of the branch's labels a version captures. :class:`AllSelection`, the default, is
            every label on the branch. A :class:`WorkflowStageSelection` applies to the ``main`` branch only.
    """

    tag: Literal["PROJECT"] = "PROJECT"
    project_id: UUID = _wire("projectUuid")
    branch_name: str = "main"
    label_selection: LabelSelection = _wire("labelSelectionMode", default_factory=AllSelection)


class StoredProjectSource(BaseDTO):
    """A source already attached to a label set.

    Args:
        id: The source identifier, used when changing its selection.
        project_id: The project.
        branch_name: The label branch a version captures.
        label_selection_mode: The selection as the platform returned it, or ``None`` when a list response omitted
            it. Read it through ``label_selection``, which refuses an omitted selection rather than reporting one.
    """

    tag: Literal["PROJECT"] = "PROJECT"
    id: UUID = _wire("uuid")
    project_id: UUID = _wire("projectUuid")
    branch_name: str
    # No default: a list response omits the selection, and the property below refuses to report one it did not get.
    label_selection_mode: Optional[StoredLabelSelection] = _wire("labelSelectionMode", default=None, repr=False)

    @property
    def label_selection(self) -> StoredLabelSelection:
        """The source's selection. :class:`AllSelection` is every label on the branch.

        Raises:
            :class:`encord.exceptions.EncordException`: The selection was omitted from a list response. Call the
                label set's ``refetch_data()`` and read its sources again.
        """
        if "label_selection_mode" not in self.model_fields_set:
            raise EncordException(
                "A listed source does not carry its selection. Call the label set's refetch_data() "
                "and read its sources again."
            )
        assert self.label_selection_mode is not None  # The platform never sends a null selection.
        return self.label_selection_mode


class UnknownSource(BaseDTOWithExtra):
    """A source of a kind this SDK version does not recognize, kept as the platform sent it.

    Args:
        tag: The kind's name. The other fields are available as attributes.
    """

    tag: str

    @dto_validator(mode="before")
    @classmethod
    def require_unfamiliar_tag(cls, values: Any) -> Any:
        # A project source with a malformed body must fail to parse, so it is refused here too.
        if isinstance(values, dict) and values.get("tag") == "PROJECT":
            raise ValueError("Expected a source with an unfamiliar tag.")
        return values


StoredSource = Union[StoredProjectSource, UnknownSource]
"""A source as the platform returns it, which may be a kind this SDK version does not recognize."""


class LabelSet(BaseDTO):
    """A label set as the platform returns it.

    Args:
        id: Unique identifier of the label set.
        sources: The project branches that feed the set. One source today. List results name each source without
            its selection; a single set carries them.
        name: Name of the label set.
        description: Description of the label set.
        origin: Where the set's labels come from.
        created_by_email: Email of the user who created the set.
        created_at: When the set was created.
    """

    id: UUID = _wire("uuid")
    sources: List[StoredSource]
    name: str
    description: str
    origin: LabelSetOrigin
    created_by_email: str
    created_at: datetime


class _SelectionPayload(BaseDTO):
    """Keep nulls so a selection is sent whole: the platform requires every filter of a stage selection, including
    the ones this SDK leaves unset."""

    def to_dict(self, by_alias: bool = True, exclude_none: bool = False) -> Dict[str, Any]:
        """Keep ``None`` by default so a stage selection's unset filters are sent as null."""
        return super().to_dict(by_alias=by_alias, exclude_none=exclude_none)


class CreateLabelSetPayload(_SelectionPayload):
    """Payload for creating a label set.

    Args:
        sources: The project branches that feed the set, each with its selection. The platform accepts one today.
        name: Name of the label set.
        description: Description of the label set.
        origin: Where the branch's labels come from.
    """

    sources: List[ProjectSource]
    name: str
    description: str
    origin: LabelSetOrigin


class UpdateLabelSetPayload(BaseDTO):
    """Payload for changing a label set's name or description. A field left as ``None`` is unchanged.

    Args:
        name: New name.
        description: New description. An empty string clears it.
    """

    name: Optional[str] = None
    description: Optional[str] = None


class SetLabelSelectionPayload(_SelectionPayload):
    """Payload for replacing one source's selection.

    Args:
        label_selection: New selection; :class:`AllSelection` captures every label on the branch.
    """

    label_selection: LabelSelection = _wire("labelSelectionMode")


class LabelSetPageParams(BaseDTO):
    """Query parameters for a paged list under a label set.

    Args:
        page_size: Maximum number of results per page.
        page_token: Token for the next page, from the previous page.
    """

    page_size: Optional[int] = None
    page_token: Optional[str] = None


class ListLabelSetsParams(LabelSetPageParams):
    """Query parameters for listing label sets.

    Args:
        project_id: Only the sets this project feeds.
        page_size: Maximum number of sets per page.
        page_token: Token for the next page, from the previous page.
    """

    project_id: Optional[UUID] = _wire("projectUuid", default=None)


class CapturedSource(BaseDTO):
    """A project branch as a version captured it, with the ontology its labels were made against at the time.

    Args:
        project_id: The project.
        branch_name: The label branch that was captured.
        ontology_id: The ontology the labels were made against.
        ontology_version_id: The ontology revision in force when the version was created. ``None`` for an ontology with no revision
            history.
    """

    tag: Literal["PROJECT"] = "PROJECT"
    project_id: UUID = _wire("projectUuid")
    branch_name: str
    ontology_id: UUID = _wire("ontologyUuid")
    ontology_version_id: Optional[UUID] = _wire("ontologyVersionUuid", default=None)


StoredCapturedSource = Union[CapturedSource, UnknownSource]
"""A captured source as the platform returns it, which may be a kind this SDK version does not recognize."""


class VersionOntology(BaseDTO):
    """The ontology definition a version's labels were made against, frozen when the version was created.

    The ontology and revision ids are on the version's ``sources``. The definition is served separately because a
    shared class can be edited without a new revision, so the ids alone cannot tell two definitions apart.

    Args:
        editor: The ontology definition, in the shape the ontology routes return.
    """

    editor: Dict[str, Any]


class LabelSetVersion(BaseDTO):
    """A version of a label set: a frozen record of the labels captured when it was created.

    Args:
        id: Unique identifier of the version.
        label_set_id: The label set the version belongs to.
        sources: What the version captured: each project branch and the ontology it used. One source today.
        version_number: Position of the version in the set, from 1.
        name: Name of the version.
        status: Lifecycle of the version.
        created_by_email: Email of the user who created the version.
        capture_started_at: When the capture started.
        capture_finished_at: When the capture finished, or ``None`` while it is building.
        label_count: How many labels the version holds. Set once the version is READY.
    """

    id: UUID = _wire("uuid")
    label_set_id: UUID = _wire("labelSetUuid")
    sources: List[StoredCapturedSource]
    version_number: int
    name: str
    status: LabelSetVersionStatus
    created_by_email: str
    capture_started_at: datetime
    capture_finished_at: Optional[datetime] = None
    label_count: Optional[int] = None


class LabelSetVersionMember(BaseDTO):
    """One label as a version holds it.

    Args:
        label_id: The label row.
        label_version: The revision of the label row that was captured.
        backing_item_id: The storage item the label was on when captured.
        data_title: Title of the data unit.
    """

    label_id: UUID = _wire("labelUuid")
    label_version: int
    backing_item_id: UUID = _wire("backingItemUuid")
    data_title: str


class CreateVersionPayload(BaseDTO):
    """Payload for creating a version.

    Args:
        name: A label for the version, shown with its number. ``None`` means the number alone.
    """

    name: Optional[str] = None


class LabelSetJob(BaseDTO):
    """A queued label set job.

    Args:
        job_id: The job, to poll for its result.
    """

    job_id: UUID = _wire("jobUuid")


class LabelSetJobPending(BaseDTO):
    """The job is queued or running. Poll again.

    Args:
        status: Always PENDING.
    """

    status: Literal[LabelSetJobStatus.PENDING] = LabelSetJobStatus.PENDING


class LabelSetJobUnknown(BaseDTO):
    """A job state this SDK version does not recognize. Treat it as not done.

    Args:
        status: UNKNOWN.
    """

    status: LabelSetJobStatus

    @dto_validator(mode="before")
    @classmethod
    def require_unfamiliar_status(cls, values: Any) -> Any:
        # A known status with a malformed body must fail to parse, so it is refused here too.
        if isinstance(values, dict) and LabelSetJobStatus(values.get("status")) is not LabelSetJobStatus.UNKNOWN:
            raise ValueError("Expected a job with an unfamiliar status.")
        return values


class VersionJobDone(BaseDTO):
    """The version job finished.

    Args:
        status: Always DONE.
        version_id: The version the job created.
    """

    status: Literal[LabelSetJobStatus.DONE] = LabelSetJobStatus.DONE
    version_id: UUID = _wire("versionUuid")


class VersionJobFailed(BaseDTO):
    """The version job failed. No version was created.

    Args:
        status: Always FAILED.
        error: Why the job failed.
    """

    status: Literal[LabelSetJobStatus.FAILED] = LabelSetJobStatus.FAILED
    error: str


VersionJob = Union[LabelSetJobPending, VersionJobDone, VersionJobFailed, LabelSetJobUnknown]
"""The state of a version job: one of pending, done, failed, or a state this SDK version does not recognize."""


class VersionJobResponse(RootModelDTO[VersionJob]):
    """Wire envelope of a version job read; ``root`` is the state."""


class CreateVersionExportPayload(BaseDTO):
    """Payload for exporting a version.

    Args:
        format: Format of the export.
    """

    format: ExportFormat = ExportFormat.JSON


class VersionExportJobDone(BaseDTO):
    """The export finished.

    Args:
        status: Always DONE.
        signed_url: A link to the archive, signed freshly on every read.
    """

    status: Literal[LabelSetJobStatus.DONE] = LabelSetJobStatus.DONE
    signed_url: str


class VersionExportJobFailed(BaseDTO):
    """The export failed. Queue it again; a repeat failure is one for support.

    Args:
        status: Always FAILED.
    """

    status: Literal[LabelSetJobStatus.FAILED] = LabelSetJobStatus.FAILED


VersionExportJob = Union[LabelSetJobPending, VersionExportJobDone, VersionExportJobFailed, LabelSetJobUnknown]
"""The state of an export job: one of pending, done, failed, or a state this SDK version does not recognize."""


class VersionExportJobResponse(RootModelDTO[VersionExportJob]):
    """Wire envelope of an export job read; ``root`` is the state."""
