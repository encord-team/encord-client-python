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
import json
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Dict

from encord.orm import base_orm
from encord.orm.formatter import Formatter


class LabelRow(base_orm.BaseORM):
    """
    A label row contains a data unit or a collection of data units and associated labels,
    and is specific to a data asset with type video or img_group:

        - A label row with a data asset of type video contains a single data unit.
        - A label row with a data asset of type img_group contains any number of data units.

    Label row ORM:

    label_hash (uid),
    dataset_hash (uid),
    dataset_title,
    data_title,
    data_type,
    data_units,
    object_answers,
    classification_answers,
    label_status

    A data unit, contained the dictionary data_units, is in the form:

        "data_units": {
            data_hash: {
                "data_hash": A data_hash (uid) string
                "data_title": A data title string
                "data_link": Signed URL expiring after 7 days,
                "data_type": Data unit type (video/mp4, image/jpeg, etc.)
                "data_fps": For video, the frame rate
                "data_sequence": Sequence number of data unit in label row.
                "labels": {
                    ...
                }
            },
            ...,
        }

    A data unit can have any number of vector labels (e.g. bounding box, polygon, keypoint) and classifications.

    Each frame-level object and classification has unique identifiers 'objectHash' and 'classificationHash'.
    Each frame-level entity has a unique feature identifier 'featureHash', defined in the editor ontology.

    The object and classification answers are contained separately from the individual data units to
    preserve space for video, sequential images, DICOM, etc.

    The objects and classifications answer dictionaries contain classification 'answers' (i.e. attributes
    that describe the object or classification). This is to avoid storing the information at every frame
    in the blurb, of particular importance for videos.

    A labels dictionary for video is in the form:
    {
        "frame": {
            "objects": {
                [{object 1}, {object 2}, ...]
            }
            "classifications": {
                [{classification 1}, {classification 2}, ...]
            }
        }
    }

    A labels dictionary for an img_group data unit is in the form:
    {
        "objects": {
            [{object 1}, {object 2}, ...]
        }
        "classifications": {
            [{classification 1}, {classification 2}, ...]
        }
    }

    The object answers dictionary is in the form:
    {
        "objectHash": {
            "objectHash": objectHash,
            "classifications": [{answer 1}, {answer 2}, ...]
        },
        ...
    }

    The classification answers dictionary is in the form:
    {
        "classificationHash": {
            "classificationHash": classificationHash,
            "classifications": [{answer 1}, {answer 2}, ...]
        },
        ...
    }

    The object actions dictionary is in the form:
    {
        "objectHash": {
            "objectHash": objectHash,
            "actions": [{answer 1}, {answer 2}, ...]
        },
        ...
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

    @classmethod
    def from_dict(cls, json_dict: Dict):
        return LabelRowMetadata(
            json_dict["label_hash"],
            json_dict["data_hash"],
            json_dict["dataset_hash"],
            json_dict["data_title"],
            json_dict["data_type"],
            LabelStatus(json_dict["label_status"]),
            AnnotationTaskStatus(json_dict["annotation_task_status"]),
        )
