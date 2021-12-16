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

import dataclasses
import json
from collections import OrderedDict
from enum import IntEnum, Enum
from typing import List, Dict

from cord.orm import base_orm
from cord.orm.formatter import Formatter


class Dataset(base_orm.BaseORM):
    """
    A dataset is a collection of data rows.

    ORM:

    title,
    description,
    dataset_type (Cord storage vs. AWS/GCP/Azure),
    data_rows: [
        {
            data_hash (uid),
            data_title,
            data_type,
        }
    ]

    """

    DB_FIELDS = OrderedDict([
        ("title", str),
        ("description", str),
        ("dataset_type", str),
        ("data_rows", (list, str))
    ])

    NON_UPDATABLE_FIELDS = {
        "dataset_type",
    }


@dataclasses.dataclass(frozen=True)
class DatasetAPIKey(Formatter):
    dataset_hash: str
    api_key: str
    title: str
    key_hash: str
    scopes: List[DatasetScope]

    @classmethod
    def from_dict(cls, json_dict: Dict):
        if isinstance(json_dict['scopes'], str):
            json_dict['scopes'] = json.loads(json_dict['scopes'])
        scopes = [DatasetScope(scope) for scope in json_dict['scopes']]
        return DatasetAPIKey(json_dict['resource_hash'], json_dict['api_key'], json_dict['title'],
                             json_dict['key_hash'], scopes)


class DatasetType(IntEnum):
    CORD_STORAGE = 0,
    AWS = 1,
    GCP = 2,
    AZURE = 3


class DatasetScope(Enum):
    READ = 'dataset.read'
    WRITE = 'dataset.write'


class DatasetData(base_orm.BaseORM):
    """
    Video base ORM.
    """

    DB_FIELDS = OrderedDict([
        ("data_hash", str),
        ("video", dict),
        ("images", list),
    ])


class SignedVideoURL(base_orm.BaseORM):
    """ A signed URL object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("signed_url", str),
        ("data_hash", str),
        ("title", str),
        ("file_link", str)
    ])


class SignedImageURL(base_orm.BaseORM):
    """ A signed URL object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("signed_url", str),
        ("data_hash", str),
        ("title", str),
        ("file_link", str)
    ])


class SignedImagesURL(base_orm.BaseListORM):
    """ A signed URL object with supporting information. """
    BASE_ORM_TYPE = SignedImageURL


class Video(base_orm.BaseORM):
    """ A video object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("data_hash", str),
        ("title", str),
        ("file_link", str),
    ])

    NON_UPDATABLE_FIELDS = {
        "data_hash",
    }


class ImageGroup(base_orm.BaseORM):
    """ An image group object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("data_hash", str),
        ("title", str),
        ("file_link", str),
    ])

    NON_UPDATABLE_FIELDS = {
        "data_hash",
    }


class Image(base_orm.BaseORM):
    """ An image object with supporting information. """
    DB_FIELDS = OrderedDict([
        ("data_hash", str),
        ("title", str),
        ("file_link", str),
    ])

    NON_UPDATABLE_FIELDS = {
        "data_hash",
    }


@dataclasses.dataclass(frozen=True)
class ImageGroupOCR:
    processed_texts: Dict


@dataclasses.dataclass(frozen=True)
class ReEncodeVideoTaskResult:
    data_hash: str
    signed_url: str
    bucket_path: str


@dataclasses.dataclass(frozen=True)
class ReEncodeVideoTask(Formatter):
    """ A re encode video object with supporting information. """
    status: str
    result: List[ReEncodeVideoTaskResult] = None

    @classmethod
    def from_dict(cls, json_dict: Dict):
        if "result" in json_dict:
            dict_results = json_dict["result"]
            results = [ReEncodeVideoTaskResult(result["data_hash"],
                                               result["signed_url"],
                                               result["bucket_path"])
                       for result in dict_results]
            return ReEncodeVideoTask(json_dict["status"], results)
        else:
            return ReEncodeVideoTask(json_dict["status"])
