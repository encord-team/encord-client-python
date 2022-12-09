#
# Copyright (c) 2020 Cord Technologies Limited
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

from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

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
            ("dataset_hash", str),
            ("dataset_title", str),
            ("data_title", str),
            ("data_type", str),
            ("data_units", dict),
            ("object_answers", dict),
            ("classification_answers", dict),
            ("object_actions", dict),
            ("label_status", str),
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


@dataclass(frozen=True)
class LabelRowMetadata(Formatter):
    """
    Contains helpful information about a LabelRow.
    """

    label_hash: str
    data_hash: str
    dataset_hash: str
    data_title: str
    data_type: str
    label_status: LabelStatus
    annotation_task_status: AnnotationTaskStatus
    is_shadow_data: bool

    @classmethod
    def from_dict(cls, json_dict: Dict) -> LabelRowMetadata:
        return LabelRowMetadata(
            json_dict["label_hash"],
            json_dict["data_hash"],
            json_dict["dataset_hash"],
            json_dict["data_title"],
            json_dict["data_type"],
            LabelStatus(json_dict["label_status"]),
            AnnotationTaskStatus(json_dict["annotation_task_status"]),
            json_dict.get("is_shadow_data", False),
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
        return dict(
            label_hash=self.label_hash,
            data_hash=self.data_hash,
            dataset_hash=self.dataset_hash,
            data_title=self.data_title,
            data_type=self.data_type,
            label_status=self.label_status.value,
            annotation_task_status=self.annotation_task_status.value,
            is_shadow_data=self.is_shadow_data,
        )
