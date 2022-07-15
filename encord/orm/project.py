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
import datetime
from collections import OrderedDict
from enum import Enum, IntEnum
from typing import Optional

from encord.orm import base_orm


class Project(base_orm.BaseORM):
    """
    DEPRECATED - prefer using the `encord.project.Project` class instead.

    A project defines a label ontology and is a collection of datasets and label rows.

    ORM:

    * title,
    * description,
    * editor_ontology,
    * ontology_hash,
    * datasets::

        [
           {
                dataset_hash (uid),
                title,
                description,
                dataset_type (internal vs. AWS/GCP/Azure),
           },
           ...
        ],
    * label_rows::

        [
            {
                label_hash (uid),
                data_hash (uid),
                dataset_hash (uid),
                dataset_title,
                data_title,
                data_type,
                label_status
            },
            ...
        ]
    * annotation_task_status

    """

    DB_FIELDS = OrderedDict(
        [
            ("project_hash", str),
            ("title", str),
            ("description", str),
            ("created_at", datetime.datetime),
            ("last_edited_at", datetime.datetime),
            ("editor_ontology", (dict, str)),
            ("datasets", (list, str)),
            ("label_rows", (list, str)),
            ("ontology_hash", str),
        ]
    )

    NON_UPDATABLE_FIELDS = {"editor_ontology", "datasets", "label_rows"}

    def get_labels_list(self):
        """
        Returns a list of all label row IDs (label_hash uid) in a project.
        """
        labels = self.to_dic().get("label_rows")
        res = []
        for label in labels:
            res.append(label.get("label_hash"))
        return res

    @property
    def project_hash(self):
        return self["project_hash"]

    @property
    def title(self):
        return self["title"]

    @property
    def description(self):
        return self["description"]

    @property
    def editor_ontology(self):
        return self["editor_ontology"]

    @property
    def datasets(self):
        return self["datasets"]

    @property
    def label_rows(self):
        return self["label_rows"]

    @property
    def ontology_hash(self):
        return self["ontology_hash"]


class ProjectCopy:
    pass


class ProjectUsers:
    pass


class ProjectDataset:
    pass


class ProjectCopyOptions(Enum):
    COLLABORATORS = "collaborators"
    DATASETS = "datasets"
    MODELS = "models"


class StringEnum(Enum):
    """
    Use this enum class if you need the helper that creates the enum instance from a string.
    """

    @classmethod
    def from_string(cls, string: str) -> Optional["StringEnum"]:
        return cls._value2member_map_.get(string)


class ReviewMode(StringEnum):
    """
    UNLABELLED:
        The labels are added to the images. However, the one person must still go over
            all of the labels before submitting them for review.
    LABELLED:
        The labels are added to the images and are marked as labelled. A reviewer will
            still need to approve those.
    REVIEWED:
        The labels are added to the images and considered reviewed. No more action is
            required from the labeler or reviewer.
    """

    UNLABELLED = "unlabelled"
    LABELLED = "labelled"
    REVIEWED = "reviewed"


class ProjectImporter(base_orm.BaseORM):
    DB_FIELDS = OrderedDict(
        [
            ("project_hash", Optional[str]),
            ("errors", list),
        ]
    )


class CvatExportType(Enum):
    PROJECT = "project"
    TASK = "task"


class ProjectImporterCvatInfo(base_orm.BaseORM):
    DB_FIELDS = OrderedDict(
        [
            ("export_type", CvatExportType),
        ]
    )
