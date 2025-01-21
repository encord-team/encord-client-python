from __future__ import annotations

import datetime
from collections import OrderedDict
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field

from encord.common.time_parser import parse_datetime
from encord.orm import base_orm
from encord.orm.base_dto import BaseDTO
from encord.orm.formatter import Formatter


class LabelRow(base_orm.BaseORM):
    """A label row contains a data unit or a collection of data units and associated
    labels, and is specific to a data asset with type ``video`` or ``img_group``:

    * A label row with a data asset of type video contains a single data unit.
    * A label row with a data asset of type img_group contains any number of data units.

    The label row ORM is as follows:

    * ``label_hash`` (uid) is the unique identifier of the label row
    * ``dataset_hash`` (uid) is the unique identifier of the dataset which contains the
      particular video or image group
    * ``dataset_title`` is the title of the dataset which contains the particular video
      or image group
    * ``data_title`` is the title of the video or image group
    * ``data_type`` either ``video`` or ``img_group`` depending on data type
    * ``data_units`` a dictionary with (key: data hash, value: data unit) pairs.
    * ``object_answers`` is a dictionary with (key: object hash, value: object answer)
      pairs.
    * ``classification_answers`` is a dictionary with (key: classification hash, value:
      classification answer) pairs.
    * ``object_actions`` is a dictionary with (key: ``<object_hash>``, value: object
      action) pairs.
    * ``label_status`` is a string indicating label status. It can take the values
      enumerated in :class:`encord.orm.label_row.LabelStatus`. *Note* that this does
      *not* reflect thes status shown in the Projects->Labels section on the web-app.

    A data unit, mentioned for the dictionary entry ``data_units`` above, has in the
    form::

        label_row = {  # The label row
            # ...
            "data_units": {
                "<data_hash>": {
                    "data_hash": "<data_hash>",  # A data_hash (uid) string
                    "data_title": "A data title",
                    "data_link": "<data_link>",  # Signed URL that expiring after 7 days
                    "data_type": "<data_type>",  # (video/mp4, image/jpeg, etc.)
                    "data_fps": 24.95,           # For video, the frame rate
                    "data_sequence": "0",        # Defines order of data units
                    "width": 640,                # The width of the content
                    "height": 610,               # The height of the content
                    "labels": {
                        # ...
                    }
                },
                # ...,
            }
        }

    A data unit can have any number of vector labels (e.g. bounding box, polygon, keypoint) and classifications.

    **Objects and classifications**

    A data unit can have any number of vector labels (e.g., bounding boxes, polygons,
    polylines, keypoints) and classifications.
    Each frame-level object and classification has unique identifiers 'objectHash' and
    'classificationHash'. Each frame-level entity has a unique feature identifier
    'featureHash', defined in the editor ontology.

    The object and classification answers are contained separately from the individual
    data units to preserve space for video, sequential images, DICOM, etc.

    The objects and classifications answer dictionaries contain classification 'answers'
    (i.e. attributes that describe the object or classification). This is to avoid
    storing the information at every frame in the blurb, of particular importance for
    videos.

    A labels dictionary for video is in the form::

        label_row["data_units"]["<data_hash>"]["labels"] = {
            "<frame_number>": {
                "objects": [
                    # { object 1 },
                    # { object 2 },
                    # ...
                ],
                "classifications": [
                    # { classification 1 },
                    # { classification 2 },
                    # ...
                ],
            }
        }

    A labels dictionary for an img_group data unit is in the form::

        label_row["data_units"]["<data_hash>"]["labels"] = {
            "objects": [
                # { object 1 },
                # { object 2 },
                # ...
            ],
            "classifications": [
                # { classification 1 },
                # { classification 2 },
                # ...
            ],
        }

    The object answers dictionary is in the form::

        label_row["object_answers"] = {
            "<object_hash>": {
                "objectHash": "<object_hash>",
                "classifications": [
                    # {answer 1},
                    # {answer 2},
                    # ...
                ]
            },
            # ...
        }

    The classification answers dictionary is in the form::

        label_row["classification_answers"] = {
            "<classification_hash>": {
                "classificationHash": "<classification_hash>",
                "classifications": [
                    # {answer 1},
                    # {answer 2},
                    # ...
                ],
            },
            # ...
        }

    The object actions dictionary is in the form::

        label_row["object_actions"] = {
            "<object_hash>": {
                "objectHash": "<object_hash>",
                "actions": [
                    # {answer 1},
                    # {answer 2},
                    # ...
                ],
            },
            # ...
        }

    """

    DB_FIELDS = OrderedDict(
        [
            ("label_hash", str),
            ("branch_name", str),
            ("created_at", str),
            ("last_edited_at", str),
            ("dataset_hash", str),
            ("dataset_title", str),
            ("data_title", str),
            ("data_hash", str),
            ("data_type", str),
            ("data_units", dict),
            ("object_answers", dict),
            ("classification_answers", dict),
            ("object_actions", dict),
            ("label_status", str),
            ("annotation_task_status", str),
            ("is_valid", bool),
        ]
    )

    NON_UPDATABLE_FIELDS = {
        "label_hash",
    }


class Review:
    pass


class AnnotationTaskStatus(Enum):
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    RETURNED = "RETURNED"
    COMPLETED = "COMPLETED"


class ShadowDataState(Enum):
    """Specifies the kind of data to fetch when working with a BenchmarkQa project"""

    ALL_DATA = "ALL_DATA"
    """ Fetch all the label rows """
    SHADOW_DATA = "SHADOW_DATA"
    """ Only fetch the label rows that were submitted against "shadow data": the annotator's view of the benchmark """
    NOT_SHADOW_DATA = "NOT_SHADOW_DATA"
    """ Only fetch the label rows for "production" data """


class LabelStatus(Enum):
    NOT_LABELLED = "NOT_LABELLED"
    LABEL_IN_PROGRESS = "LABEL_IN_PROGRESS"
    LABELLED = "LABELLED"
    REVIEW_IN_PROGRESS = "REVIEW_IN_PROGRESS"
    REVIEWED = "REVIEWED"
    REVIEWED_TWICE = "REVIEWED_TWICE"

    MISSING_LABEL_STATUS = "_MISSING_LABEL_STATUS_"
    """
    This value will be displayed if the Encord platform has a new label status and your SDK version does not understand
    it yet. Please update your SDK to the latest version.
    """

    @classmethod
    def _missing_(cls, value: Any) -> LabelStatus:
        return cls.MISSING_LABEL_STATUS


@dataclass(frozen=True)
class WorkflowGraphNode:
    uuid: str
    title: str

    @classmethod
    def from_optional_dict(cls, json_dict: Optional[Dict]) -> Optional[WorkflowGraphNode]:
        if json_dict is None:
            return None
        return WorkflowGraphNode(uuid=json_dict["uuid"], title=json_dict["title"])


@dataclass(frozen=True)
class LabelRowMetadata(Formatter):
    """Contains helpful information about a label row."""

    label_hash: Optional[str]
    """Only present if the label row is initiated"""
    created_at: Optional[datetime.datetime]
    """Only present if the label row is initiated"""
    last_edited_at: Optional[datetime.datetime]
    """Only present if the label row is initiated"""
    branch_name: str
    """Only present if the label row is initiated or branch_name is set specifically"""

    data_hash: str
    dataset_hash: str
    dataset_title: str
    data_title: str
    data_type: str
    data_link: Optional[str]
    """Can be `None` for label rows of image groups or DICOM series."""
    label_status: LabelStatus
    """Can be `None` for TMS2 projects"""
    annotation_task_status: Optional[AnnotationTaskStatus]
    """Only available for TMS2 project"""
    workflow_graph_node: Optional[WorkflowGraphNode]
    is_shadow_data: bool

    """Only available for the VIDEO and AUDIO data_type"""
    frames_per_second: Optional[float]
    number_of_frames: int
    duration: Optional[float]

    """Only available for the VIDEO data_type"""
    height: Optional[int]
    width: Optional[int]

    """Only available for the AUDIO data_type"""
    audio_sample_rate: Optional[int]
    audio_codec: Optional[str]
    audio_bit_depth: Optional[int]
    audio_num_channels: Optional[int]

    priority: Optional[float] = None
    """Only available for not complete tasks"""
    client_metadata: Optional[dict] = None
    images_data: Optional[list] = None
    file_type: Optional[str] = None
    """Only available for certain read requests"""
    is_valid: bool = True

    backing_item_uuid: Optional[UUID] = None

    @classmethod
    def from_dict(cls, json_dict: Dict) -> LabelRowMetadata:
        created_at = json_dict.get("created_at", None)
        if created_at is not None:
            created_at = parse_datetime(created_at)
        last_edited_at = json_dict.get("last_edited_at", None)
        if last_edited_at is not None:
            last_edited_at = parse_datetime(last_edited_at)

        annotation_task_status = (
            AnnotationTaskStatus(json_dict["annotation_task_status"])
            if json_dict.get("annotation_task_status", None) is not None
            else None
        )

        return LabelRowMetadata(
            label_hash=json_dict.get("label_hash", None),
            created_at=created_at,
            last_edited_at=last_edited_at,
            data_hash=json_dict["data_hash"],
            dataset_hash=json_dict["dataset_hash"],
            dataset_title=json_dict["dataset_title"],
            data_title=json_dict["data_title"],
            data_type=json_dict["data_type"],
            data_link=json_dict["data_link"],
            label_status=LabelStatus(json_dict["label_status"]),
            annotation_task_status=annotation_task_status,
            workflow_graph_node=WorkflowGraphNode.from_optional_dict(json_dict.get("workflow_graph_node")),
            is_shadow_data=json_dict.get("is_shadow_data", False),
            number_of_frames=json_dict["number_of_frames"],
            duration=json_dict.get("duration", None),
            frames_per_second=json_dict.get("frames_per_second", None),
            audio_codec=json_dict.get("audio_codec", None),
            audio_bit_depth=json_dict.get("audio_bit_depth", None),
            audio_num_channels=json_dict.get("audio_num_channels", None),
            audio_sample_rate=json_dict.get("audio_sample_rate", None),
            height=json_dict.get("height"),
            width=json_dict.get("width"),
            priority=json_dict.get("priority"),
            client_metadata=json_dict.get("client_metadata", None),
            images_data=json_dict.get("images_data", None),
            file_type=json_dict.get("file_type"),
            is_valid=bool(json_dict.get("is_valid", True)),
            branch_name=json_dict["branch_name"],
            backing_item_uuid=UUID(json_dict["backing_item_uuid"])
            if json_dict.get("backing_item_uuid", None) is not None
            else None,
        )

    @classmethod
    def from_list(cls, json_list: list) -> List[LabelRowMetadata]:
        ret = []
        for i in json_list:
            ret.append(cls.from_dict(i))
        return ret

    def to_dict(self) -> dict:
        """Returns:
        The dict equivalent of LabelRowMetadata.
        """

        def transform(value: Any):
            if isinstance(value, Enum):
                return value.value
            elif isinstance(value, datetime.datetime):
                return value.isoformat()
            return value

        return {k: transform(v) for k, v in asdict(self).items()}


class LabelValidationState(BaseDTO):
    label_hash: str
    branch_name: str
    version: int
    is_valid: bool
    errors: List[str]


class WorkflowGraphNodeDTO(BaseDTO):
    uuid: str
    title: str


class LabelRowMetadataDTO(BaseDTO):
    """Contains helpful information about a label row."""

    label_hash: Optional[str] = Field(default=None, alias="label_uuid")
    """Only present if the label row is initiated"""
    created_at: Optional[datetime.datetime] = None
    """Only present if the label row is initiated"""
    last_edited_at: Optional[datetime.datetime] = None
    """Only present if the label row is initiated"""
    branch_name: str
    """Only present if the label row is initiated or branch_name is set specifically"""

    data_hash: str = Field(alias="data_uuid")
    dataset_hash: str = Field(alias="dataset_uuid")
    dataset_title: str
    data_title: str
    data_type: str
    data_link: Optional[str] = None

    """Can be `None` for label rows of image groups or DICOM series."""
    label_status: LabelStatus
    """Can be `None` for TMS2 projects"""
    annotation_task_status: Optional[AnnotationTaskStatus] = None
    """Only available for TMS2 project"""
    workflow_graph_node: Optional[WorkflowGraphNode] = None
    is_shadow_data: bool = False

    """Only available for the VIDEO and AUDIO data_type"""
    frames_per_second: Optional[float]
    number_of_frames: int
    duration: Optional[float]

    """Only available for the VIDEO data_type"""
    height: Optional[int]
    width: Optional[int]

    """Only available for the AUDIO data_type"""
    audio_sample_rate: Optional[int]
    audio_codec: Optional[str]
    audio_bit_depth: Optional[int]
    audio_num_channels: Optional[int]

    priority: Optional[float] = None
    """Only available for not complete tasks"""
    client_metadata: Optional[Dict[str, Any]] = None
    images_data: Optional[List[Any]] = None
    file_type: Optional[str] = None
    """Only available for certain read requests"""
    is_valid: bool = True

    backing_item_uuid: Optional[UUID] = None


def label_row_metadata_dto_to_label_row_metadata(label_row_metadata_dto: LabelRowMetadataDTO) -> LabelRowMetadata:
    return LabelRowMetadata(
        label_hash=label_row_metadata_dto.label_hash,
        created_at=label_row_metadata_dto.created_at,
        last_edited_at=label_row_metadata_dto.last_edited_at,
        data_hash=label_row_metadata_dto.data_hash,
        dataset_hash=label_row_metadata_dto.dataset_hash,
        dataset_title=label_row_metadata_dto.dataset_title,
        data_title=label_row_metadata_dto.data_title,
        data_type=label_row_metadata_dto.data_type,
        data_link=label_row_metadata_dto.data_link,
        label_status=label_row_metadata_dto.label_status,
        annotation_task_status=label_row_metadata_dto.annotation_task_status,
        workflow_graph_node=label_row_metadata_dto.workflow_graph_node,
        is_shadow_data=label_row_metadata_dto.is_shadow_data,
        number_of_frames=label_row_metadata_dto.number_of_frames,
        duration=label_row_metadata_dto.duration,
        audio_sample_rate=label_row_metadata_dto.audio_sample_rate,
        audio_codec=label_row_metadata_dto.audio_codec,
        audio_bit_depth=label_row_metadata_dto.audio_bit_depth,
        audio_num_channels=label_row_metadata_dto.audio_num_channels,
        frames_per_second=label_row_metadata_dto.frames_per_second,
        height=label_row_metadata_dto.height,
        width=label_row_metadata_dto.width,
        priority=label_row_metadata_dto.priority,
        client_metadata=label_row_metadata_dto.client_metadata,
        images_data=label_row_metadata_dto.images_data,
        file_type=label_row_metadata_dto.file_type,
        is_valid=label_row_metadata_dto.is_valid,
        branch_name=label_row_metadata_dto.branch_name,
        backing_item_uuid=label_row_metadata_dto.backing_item_uuid,
    )
