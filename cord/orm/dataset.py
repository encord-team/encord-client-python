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
from datetime import datetime
from dateutil import parser
import json
from collections import OrderedDict
from enum import IntEnum, Enum
from typing import List, Dict, Optional

from cord.constants.enums import DataType
from cord.orm import base_orm
from cord.orm.formatter import Formatter


@dataclasses.dataclass(frozen=True)
class DataRow(Formatter):
    uid: str
    title: str
    type: DataType
    created_at: datetime

    @classmethod
    def from_dict(cls, json_dict: Dict) -> DataRow:
        return DataRow(
            uid=json_dict["data_hash"],
            title=json_dict["data_title"],
            type=DataType.from_string(json_dict["data_type"]),
            created_at=parser.parse(json_dict["created_at"]),
        )

    @classmethod
    def from_dict_list(cls, json_list: List) -> List[DataRow]:
        ret: List[DataRow] = list()
        for json_dict in json_list:
            ret.append(cls.from_dict(json_dict))
        return ret


@dataclasses.dataclass(frozen=True)
class Dataset(Formatter):
    title: str
    description: Optional[str]
    storage_location: StorageLocation
    data_rows: List[DataRow]

    @classmethod
    def from_dict(cls, json_dict: Dict) -> Dataset:
        return Dataset(
            title=json_dict["title"],
            description=json_dict["description"],
            storage_location=StorageLocation.from_str(json_dict["dataset_type"]),
            data_rows=DataRow.from_dict_list(json_dict.get("data_rows", [])),
        )


@dataclasses.dataclass(frozen=True)
class DatasetAPIKey(Formatter):
    dataset_uid: str
    api_key: str
    title: str
    key_hash: str
    scopes: List[DatasetScope]

    @classmethod
    def from_dict(cls, json_dict: Dict) -> DatasetAPIKey:
        if isinstance(json_dict["scopes"], str):
            json_dict["scopes"] = json.loads(json_dict["scopes"])
        scopes = [DatasetScope(scope) for scope in json_dict["scopes"]]
        return DatasetAPIKey(
            json_dict["resource_hash"],
            json_dict["api_key"],
            json_dict["title"],
            json_dict["key_hash"],
            scopes,
        )


@dataclasses.dataclass(frozen=True)
class CreateDatasetResponse(Formatter):
    title: str
    type: StorageLocation
    dataset_uid: str
    user_uid: str

    @classmethod
    def from_dict(cls, json_dict: Dict) -> CreateDatasetResponse:
        return CreateDatasetResponse(
            title=json_dict["title"],
            type=StorageLocation(json_dict["type"]),
            dataset_uid=json_dict["dataset_hash"],
            user_uid=json_dict["user_hash"],
        )


class StorageLocation(IntEnum):
    CORD_STORAGE = (0,)
    AWS = (1,)
    GCP = (2,)
    AZURE = 3

    @staticmethod
    def from_str(string_location: str) -> StorageLocation:
        if string_location == "CORD_STORAGE":
            return StorageLocation.CORD_STORAGE
        if string_location == "AWS_S3":
            return StorageLocation.AWS
        if string_location == "GCP_STR":
            return StorageLocation.GCP
        if string_location == "AZURE_STR":
            return StorageLocation.AZURE
        raise TypeError(f"Invalid storage location string: `{string_location}`")


class DatasetScope(Enum):
    READ = "dataset.read"
    WRITE = "dataset.write"


class DatasetData(base_orm.BaseORM):
    """
    Video base ORM.
    """

    DB_FIELDS = OrderedDict(
        [
            ("data_hash", str),
            ("video", dict),
            ("images", list),
        ]
    )


class SignedVideoURL(base_orm.BaseORM):
    """A signed URL object with supporting information."""

    DB_FIELDS = OrderedDict([("signed_url", str), ("data_hash", str), ("title", str), ("file_link", str)])


class SignedImageURL(base_orm.BaseORM):
    """A signed URL object with supporting information."""

    DB_FIELDS = OrderedDict([("signed_url", str), ("data_hash", str), ("title", str), ("file_link", str)])


class SignedImagesURL(base_orm.BaseListORM):
    """A signed URL object with supporting information."""

    BASE_ORM_TYPE = SignedImageURL


class Video(base_orm.BaseORM):
    """A video object with supporting information."""

    DB_FIELDS = OrderedDict(
        [
            ("data_hash", str),
            ("title", str),
            ("file_link", str),
        ]
    )

    NON_UPDATABLE_FIELDS = {
        "data_hash",
    }


class ImageGroup(base_orm.BaseORM):
    """An image group object with supporting information."""

    DB_FIELDS = OrderedDict(
        [
            ("data_hash", str),
            ("title", str),
            ("file_link", str),
        ]
    )

    NON_UPDATABLE_FIELDS = {
        "data_hash",
    }


class Image(base_orm.BaseORM):
    """An image object with supporting information."""

    DB_FIELDS = OrderedDict(
        [
            ("data_hash", str),
            ("title", str),
            ("file_link", str),
        ]
    )

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
    """A re encode video object with supporting information."""

    status: str
    result: List[ReEncodeVideoTaskResult] = None

    @classmethod
    def from_dict(cls, json_dict: Dict):
        if "result" in json_dict:
            dict_results = json_dict["result"]
            results = [
                ReEncodeVideoTaskResult(result["data_hash"], result["signed_url"], result["bucket_path"])
                for result in dict_results
            ]
            return ReEncodeVideoTask(json_dict["status"], results)
        else:
            return ReEncodeVideoTask(json_dict["status"])
