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
import datetime
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union

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
            ("source_projects", list),
        ]
    )

    NON_UPDATABLE_FIELDS = {"editor_ontology", "datasets", "label_rows"}

    def get_labels_list(self) -> List[Optional[str]]:
        """
        Returns a list of all optional label row IDs (label_hash uid) in a project. If no `label_hash` is found,
        a `None` value is appended. This can be useful for working with fetching additional label row data via
        :meth:`encord.project.Project.get_label_rows` for example.

        .. code::

                project = client_instance.get_project(<project_hash>)
                project_orm = project.get_project()

                labels_list = project_orm.get_labels_list()
                created_labels_list = []
                for label in labels_list:
                    if label is not None:  # None values will fail the operation
                        created_labels_list.append(label)

                label_rows = project.get_label_rows(created_labels_list, get_signed_url=False)
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

    @property
    def source_projects(self):
        return self["source_projects"]


class ProjectCopy:
    pass


class ProjectUsers:
    pass


class ProjectDataset:
    pass


class ProjectCopyOptions(str, Enum):
    COLLABORATORS = "collaborators"
    DATASETS = "datasets"
    MODELS = "models"
    LABELS = "labels"


class ReviewApprovalState(str, Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    DELETED = "DELETED"
    NOT_SELECTED_FOR_REVIEW = "NOT_SELECTED_FOR_REVIEW"


class CopyDatasetAction(str, Enum):
    ATTACH = "ATTACH"
    """ Attach the datasets associated with the original project to the copy project. """
    CLONE = "CLONE"
    """ Clone the data units from the associated datasets into a new dataset an attach it to the copy project. """


@dataclass
class CopyDatasetOptions:
    """Options for copying the datasets associated with a project."""

    action: CopyDatasetAction = CopyDatasetAction.ATTACH
    """
    One of `CopyDatasetAction.ATTACH` or `CopyDatasetAction.CLONE`. (defaults to ATTACH)
    """
    dataset_title: Optional[str] = None
    dataset_description: Optional[str] = None
    datasets_to_data_hashes_map: Dict[str, List[str]] = field(default_factory=dict)
    """ A dictionary of `{ <dataset_hash>: List[<data_unit_hash>]}`.
    When provided with a CLONE action this will filter the copied data units.
    When combined with `CopyLabelsOptions`, only labels from specific data units will be copied.
    """


@dataclass
class CopyLabelsOptions:
    """Options for copying the labels associated with a project."""

    accepted_label_hashes: Optional[List[str]] = None
    """ A list of label hashes that will be copied to the new project  """
    accepted_label_statuses: Optional[List[ReviewApprovalState]] = None
    """ A list of label statuses to filter the labels copied to the new project, defined in `ReviewApprovalState`"""


@dataclass
class CopyProjectPayload:
    """WARN: do not use, this is only for internal purpose."""

    @dataclass
    class _CopyLabelsOptions:
        datasets_to_data_hashes_map: Dict[str, List[str]] = field(default_factory=dict)
        accepted_label_hashes: Optional[List[str]] = None
        accepted_label_statuses: Optional[List[ReviewApprovalState]] = None
        create_new_dataset: Optional[bool] = None

    @dataclass
    class _ProjectCopyMetadata:
        project_title: Optional[str] = None
        project_description: Optional[str] = None
        dataset_title: Optional[str] = None
        dataset_description: Optional[str] = None

    copy_project_options: List[ProjectCopyOptions] = field(default_factory=list)
    copy_labels_options: Optional[_CopyLabelsOptions] = None
    project_copy_metadata: Optional[_ProjectCopyMetadata] = None


class ProjectWorkflowType(Enum):
    MANUAL_QA = "manual"
    BENCHMARK_QA = "benchmark"


class ManualReviewWorkflowSettings:
    """Sets the project QA workflow to "manual reviews". There are currently no available settings for this workflow"""

    pass


@dataclass
class BenchmarkQaWorkflowSettings:
    """Sets the project QA workflow to "Automatic", with benchmark data being presented to all the annotators"""

    source_projects: List[str] = field(default_factory=list)
    """
    For Benchmark QA projects, a list of project ids (project_hash-es)
        that contain the benchmark source data
    """


ProjectWorkflowSettings = Union[ManualReviewWorkflowSettings, BenchmarkQaWorkflowSettings]
"""
A variant type that allows you to select the type of quality assurance workflow for the project,
and configure it.

Currently one of:
    :class:`ManualReviewWorkflowSettings`: a workflow with optional manual reviews
    :class:`BenchmarkQaWorkflowSettings`: annotators are presented with "benchmark" or "honeypot" data
"""


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
