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
import pprint
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set, TypeVar, Union

import dateutil


def pretty_print(data):
    return pprint.pformat(data, indent=4, width=10)


class APIKeyScopes(Enum):
    """
    The APIKeyScope is used to provide specific access rights to a project through
    :meth:`.EncordUserClient.create_project_api_key`. The options are a follows:

        * ``LABEL_READ``: access to
          :ref:`tutorials/projects:Getting label rows`
        * ``LABEL_WRITE``: access to
          :ref:`tutorials/projects:Saving label rows`
        * ``MODEL_INFERENCE``: access to
          :ref:`tutorials/projects:Inference`
        * ``MODEL_TRAIN``: access to
          :ref:`tutorials/projects:Creating a model row` and
          :ref:`tutorials/projects:Training`
        * ``LABEL_LOGS_READ``: access to
          :ref:`tutorials/projects:Reviewing label logs`
        * ``ALGO_LIBRARY``: access to algorithms like
          :ref:`tutorials/projects:Object interpolation`

    """

    LABEL_READ = "label.read"
    LABEL_WRITE = "label.write"
    MODEL_INFERENCE = "model.inference"
    MODEL_TRAIN = "model.train"
    LABEL_LOGS_READ = "label_logs.read"
    ALGO_LIBRARY = "algo.library"


@dataclass
class LocalImport:
    """
    file_path: Supply the path of the exported folder which contains the images and `annotations.xml` file. Make
    sure to select "Save images" when exporting your CVAT Task or Project.
    """

    file_path: str


ImportMethod = Union[LocalImport]
"""Using images/videos in cloud storage as an alternative import method will be supported in the future."""


@dataclass
class Issue:
    """
    For each `issue_type` there may be multiple occurrences which are documented in the `instances`. The `instances`
    list can provide additional information on how the issue was encountered. If there is no additional information
    available, the `instances` list will be empty.
    """

    issue_type: str
    instances: List[str]


@dataclass
class Issues:
    """
    Any issues that came up during importing a project. These usually come from incompatibilities between data saved
    on different platforms.
    """

    errors: List[Issue]
    warnings: List[Issue]
    infos: List[Issue]

    @staticmethod
    def from_dict(d: dict) -> "Issues":
        errors, warnings, infos = [], [], []
        for error in d["errors"]:
            issue = Issue(issue_type=error["issue_type"], instances=error["instances"])
            errors.append(issue)
        for warning in d["warnings"]:
            issue = Issue(issue_type=warning["issue_type"], instances=warning["instances"])
            warnings.append(issue)
        for info in d["infos"]:
            issue = Issue(issue_type=info["issue_type"], instances=info["instances"])
            infos.append(issue)
        return Issues(errors=errors, warnings=warnings, infos=infos)


@dataclass
class CvatImporterSuccess:
    project_hash: str
    dataset_hash: str
    issues: Issues


@dataclass
class CvatImporterError:
    dataset_hash: str
    issues: Issues


def parse_datetime(key, val):
    if not val:
        return None
    if isinstance(val, str):
        return dateutil.parser.isoparse(val)
    if isinstance(val, datetime.datetime):
        return val.isoformat()
    else:
        raise ValueError(f"Value for {key} should be a datetime")


T = TypeVar("T")


def optional_set_to_list(s: Optional[Set[T]]) -> Optional[List[T]]:
    if s is None:
        return s
    else:
        return list(s)
