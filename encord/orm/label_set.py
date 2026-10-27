from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from encord.orm.base_dto import BaseDTO, Field


class LabelSetLabellingStatus(str, Enum):
    """Labelling status a filtered label selection can be narrowed to.

    **Values**:

    - **NOT_LABELLED:** Data units with no labels yet.
    - **IN_PROGRESS:** Data units with labels that are still being worked on.
    - **LABELLED:** Data units whose labelling is complete.
    """

    NOT_LABELLED = "NOT_LABELLED"
    IN_PROGRESS = "IN_PROGRESS"
    LABELLED = "LABELLED"


class SelectiveLabelSelection(BaseDTO):
    """Select the labels of an explicit list of data units.

    Args:
        data_hashes: Data hashes of the data units whose labels the label set captures.
    """

    tag: Literal["SELECTIVE"] = "SELECTIVE"
    data_hashes: List[str]


class FilteredLabelSelection(BaseDTO):
    """Select the labels of the data units that match a filter.

    Args:
        data_title_search: Substring matched against data titles and dataset titles. Empty matches everything.
        filter_graph_node_uuid: UUIDs of workflow stages to restrict to. Empty means any stage.
        filter_labelling_status: Labelling status to restrict to. ``None`` means any status.
    """

    tag: Literal["FILTERED"] = "FILTERED"
    data_title_search: str = ""
    filter_graph_node_uuid: List[UUID] = Field(default_factory=list)
    filter_labelling_status: Optional[LabelSetLabellingStatus] = None


LabelSelectionMode = Union[SelectiveLabelSelection, FilteredLabelSelection]
"""Which labels a label set captures at each cut. ``None`` means every label on the project's main branch."""


class LabelSetOrigin(str, Enum):
    """How a label set came to exist.

    **Values**:

    - **WORKFLOW:** Created from a project's workflow.
    - **IMPORT:** Created from an import.
    - **UNKNOWN:** An unrecognised origin from a newer API version. Please update your SDK.
    """

    WORKFLOW = "WORKFLOW"
    IMPORT = "IMPORT"

    UNKNOWN = "_unknown_"

    @classmethod
    def _missing_(cls, value: Any) -> "LabelSetOrigin":
        """Return UNKNOWN for any unrecognised origin values."""
        return cls.UNKNOWN


class LabelSetVersionStatus(str, Enum):
    """Lifecycle state of a label set version.

    **Values**:

    - **BUILDING:** The version is still being captured.
    - **READY:** The capture finished and the members are final.
    - **FAILED:** The capture failed. The version has no members.
    - **UNKNOWN:** An unrecognised status from a newer API version. Please update your SDK.
    """

    BUILDING = "BUILDING"
    READY = "READY"
    FAILED = "FAILED"

    UNKNOWN = "_unknown_"

    @classmethod
    def _missing_(cls, value: Any) -> "LabelSetVersionStatus":
        """Return UNKNOWN for any unrecognised status values."""
        return cls.UNKNOWN


class ListLabelSetsParams(BaseDTO):
    """Query parameters for listing label sets.

    Args:
        project_hash: Restrict the list to the label sets fed by this project.
        limit: Maximum number of label sets per page, 1 to 100.
        page_token: Token for fetching the next page of results from a previous call.
    """

    project_hash: Optional[UUID] = None
    limit: Optional[int] = None
    page_token: Optional[str] = None


class ListLabelSetVersionsParams(BaseDTO):
    """Query parameters for listing versions of a label set, or members of a version.

    Args:
        limit: Maximum number of results per page, 1 to 100.
        page_token: Token for fetching the next page of results from a previous call.
    """

    limit: Optional[int] = None
    page_token: Optional[str] = None


class UpdateLabelSetPayload(BaseDTO):
    """Payload for replacing a label set's configuration.

    The server treats this as a full replacement. An omitted ``label_selection_mode`` clears the selection
    and an omitted ``trigger`` resets it to manual, so a caller must send the current values back for
    anything that should stay.

    Args:
        name: Name of the label set.
        description: Description of the label set.
        trigger: Cut trigger as the server returned it. Passed through unchanged.
        label_selection_mode: Which labels each cut captures. ``None`` means every label on main.
    """

    name: str
    description: str = ""
    trigger: Dict[str, Any] = Field(default_factory=lambda: {"type": "MANUAL"})
    label_selection_mode: Optional[LabelSelectionMode] = None


class CreateLabelSetPayload(UpdateLabelSetPayload):
    """Payload for creating a label set.

    Args:
        project_hash: The project whose main branch feeds the label set.
    """

    project_hash: UUID


class CutLabelSetVersionPayload(BaseDTO):
    """Payload for cutting a new version of a label set.

    Args:
        name: Name of the version. Omitted means ``v{version_number}``.
    """

    name: Optional[str] = None


class LabelSetSummary(BaseDTO):
    """A label set as the list endpoint returns it: everything but the label selection.

    Args:
        uuid: Unique identifier of the label set.
        project_hash: The project whose main branch feeds the label set.
        branch_name: Name of the branch the labels are read from.
        name: Name of the label set.
        description: Description of the label set.
        origin: How the label set came to exist.
        trigger: Cut trigger as the server returned it. Not interpreted by the SDK.
        created_by: Hash of the user who created the label set.
        created_at: When the label set was created.
    """

    uuid: UUID = Field(alias="id")
    project_hash: UUID
    branch_name: str
    name: str
    description: str
    origin: LabelSetOrigin
    trigger: Dict[str, Any]
    created_by: str
    created_at: datetime


class LabelSet(LabelSetSummary):
    """A label set as the get, create and update endpoints return it.

    Args:
        label_selection_mode: Which labels each cut captures. ``None`` means every label on main.
    """

    label_selection_mode: Optional[LabelSelectionMode] = None


class LabelSetVersion(BaseDTO):
    """A version cut from a label set.

    Args:
        uuid: Unique identifier of the version.
        label_set_uuid: The label set the version was cut from.
        version_number: Position of the version within the label set, starting at 1.
        name: Name of the version.
        status: Lifecycle state of the version.
        trigger_type: What caused the cut, as the server returned it.
        created_by: Hash of the user who cut the version.
        capture_started_at: When the capture started.
        capture_finished_at: When the capture finished. ``None`` while the version is building.
        label_count: Number of labels captured. ``None`` until the version is ready.
    """

    uuid: UUID = Field(alias="id")
    label_set_uuid: UUID = Field(alias="labelSetId")
    version_number: int
    name: str
    status: LabelSetVersionStatus
    trigger_type: str
    created_by: str
    capture_started_at: datetime
    capture_finished_at: Optional[datetime] = None
    label_count: Optional[int] = None


class LabelSetVersionMember(BaseDTO):
    """A label row frozen into a label set version.

    Args:
        label_hash: Hash of the label row.
        label_version: Revision of the label row the version captured.
        backing_item_uuid: Storage item behind the data unit, if there is one.
        data_hash: Hash of the data unit.
        data_title: Title of the data unit.
    """

    label_hash: str
    label_version: int
    backing_item_uuid: Optional[UUID] = None
    data_hash: str
    data_title: str
