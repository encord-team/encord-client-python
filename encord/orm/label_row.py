#
# Copyright (c) 2023 Cord Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from __future__ import annotations

import datetime
from collections import OrderedDict
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from encord.orm import base_orm
from encord.orm.formatter import Formatter


class LabelRow(base_orm.BaseORM):
    """
    A label row contains a data unit or a collection of data units and associated
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
    """
    Contains helpful information about a label row.
    """

    label_hash: Optional[str]
    """Only present if the label row is initiated"""
    created_at: Optional[datetime.datetime]
    """Only present if the label row is initiated"""
    last_edited_at: Optional[datetime.datetime]
    """Only present if the label row is initiated"""

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
    number_of_frames: int
    duration: Optional[float]
    """Only available for the VIDEO data_type"""
    frames_per_second: Optional[int]
    """Only available for the VIDEO data_type"""
    height: Optional[int]
    width: Optional[int]

    @classmethod
    def from_dict(cls, json_dict: Dict) -> LabelRowMetadata:
        created_at = json_dict.get("created_at", None)
        if created_at is not None:
            created_at = datetime.datetime.fromisoformat(created_at)
        last_edited_at = json_dict.get("last_edited_at", None)
        if last_edited_at is not None:
            last_edited_at = datetime.datetime.fromisoformat(last_edited_at)

        annotation_task_status = (
            AnnotationTaskStatus(json_dict["annotation_task_status"])
            if json_dict["annotation_task_status"] is not None
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
            height=json_dict.get("height"),
            width=json_dict.get("width"),
        )

    @classmethod
    def from_list(cls, json_list: list) -> List[LabelRowMetadata]:
        ret = []
        for i in json_list:
            ret.append(cls.from_dict(i))
        return ret

    def to_dict(self) -> dict:
        """
        Returns:
            The dict equivalent of LabelRowMetadata.
        """

        def transform(value: Any):
            if isinstance(value, Enum):
                return value.value
            elif isinstance(value, datetime.datetime):
                return value.isoformat()
            return value

        return {k: transform(v) for k, v in asdict(self).items()}
