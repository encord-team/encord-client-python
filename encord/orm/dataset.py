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
from datetime import datetime
from enum import Enum, IntEnum
from typing import Dict, List, Optional

from dateutil import parser

from encord.constants.enums import DataType
from encord.orm import base_orm
from encord.orm.formatter import Formatter

DATETIME_STRING_FORMAT = "%Y-%m-%d %H:%M:%S"


class DatasetUserRole(IntEnum):
    ADMIN = 0
    USER = 1


@dataclasses.dataclass
class DataClientMetadata:
    payload: dict


class DataRow(dict, Formatter):
    def __init__(
        self,
        uid: str,
        title: str,
        data_type: DataType,
        created_at: datetime,
        client_metadata: Optional[dict],
    ):
        """
        This class has dict-style accessors for backwards compatibility.
        Clients who are using this class for the first time are encouraged to use the property accessors and setters
        instead of the underlying dictionary.
        The mixed use of the `dict` style member functions and the property accessors and setters is discouraged.

        WARNING: Do NOT use the `.data` member of this class. Its usage could corrupt the correctness of the
        datastructure.
        """
        super().__init__(
            {
                "data_hash": uid,
                "data_title": title,
                "data_type": data_type.to_upper_case_string(),
                "created_at": created_at.strftime(DATETIME_STRING_FORMAT),
                "client_metadata": client_metadata,
            }
        )

    @property
    def uid(self) -> str:
        return self["data_hash"]

    @uid.setter
    def uid(self, value: str) -> None:
        self["data_hash"] = value

    @property
    def title(self) -> str:
        return self["data_title"]

    @title.setter
    def title(self, value: str) -> None:
        self["data_title"] = value

    @property
    def data_type(self) -> DataType:
        return DataType.from_upper_case_string(self["data_type"])

    @data_type.setter
    def data_type(self, value: DataType) -> None:
        self["data_type"] = value.to_upper_case_string()

    @property
    def created_at(self) -> datetime:
        return parser.parse(self["created_at"])

    @created_at.setter
    def created_at(self, value: datetime) -> None:
        """Datetime will trim milliseconds for backwards compatibility."""
        self["created_at"] = value.strftime(DATETIME_STRING_FORMAT)

    @property
    def client_metadata(self) -> Optional[dict]:
        """
        Custom client metadata. This is null if it is disabled via the
        :class:`encord.orm.dataset.DatasetAccessSettings`
        """
        return self["client_metadata"]

    @classmethod
    def from_dict(cls, json_dict: Dict) -> DataRow:
        data_type = DataType.from_upper_case_string(json_dict["data_type"])

        return DataRow(
            uid=json_dict["data_hash"],
            title=json_dict["data_title"],
            # The API server currently returns upper cased DataType strings.
            data_type=data_type,
            created_at=parser.parse(json_dict["created_at"]),
            client_metadata=json_dict["client_metadata"],
        )

    @classmethod
    def from_dict_list(cls, json_list: List) -> List[DataRow]:
        ret: List[DataRow] = list()
        for json_dict in json_list:
            ret.append(cls.from_dict(json_dict))
        return ret


@dataclasses.dataclass(frozen=True)
class DatasetInfo:
    """
    This class represents a dataset in the context of listing
    """

    dataset_hash: str
    user_hash: str
    title: str
    description: str
    type: int
    created_at: datetime
    last_edited_at: datetime


class Dataset(dict, Formatter):
    def __init__(
        self,
        title: str,
        storage_location: str,
        data_rows: List[DataRow],
        dataset_hash: str,
        description: Optional[str] = None,
    ):
        """
        DEPRECATED - prefer using the :class:`encord.dataset.Dataset` class instead.

        This class has dict-style accessors for backwards compatibility.
        Clients who are using this class for the first time are encouraged to use the property accessors and setters
        instead of the underlying dictionary.
        The mixed use of the `dict` style member functions and the property accessors and setters is discouraged.

        WARNING: Do NOT use the `.data` member of this class. Its usage could corrupt the correctness of the
        datastructure.
        """
        super().__init__(
            {
                "dataset_hash": dataset_hash,
                "title": title,
                "description": description,
                "dataset_type": storage_location,
                "data_rows": data_rows,
            }
        )

    @property
    def dataset_hash(self) -> str:
        return self["dataset_hash"]

    @property
    def title(self) -> str:
        return self["title"]

    @title.setter
    def title(self, value: str) -> None:
        self["title"] = value

    @property
    def description(self) -> str:
        return self["description"]

    @description.setter
    def description(self, value: str) -> None:
        self["description"] = value

    @property
    def storage_location(self) -> StorageLocation:
        return StorageLocation.from_str(self["dataset_type"])

    @storage_location.setter
    def storage_location(self, value: StorageLocation) -> None:
        self["dataset_type"] = value.get_str()

    @property
    def data_rows(self) -> List[DataRow]:
        return self["data_rows"]

    @data_rows.setter
    def data_rows(self, value: List[DataRow]) -> None:
        self["data_rows"] = value

    @classmethod
    def from_dict(cls, json_dict: Dict) -> Dataset:
        return Dataset(
            title=json_dict["title"],
            description=json_dict["description"],
            storage_location=json_dict["dataset_type"],
            dataset_hash=json_dict["dataset_hash"],
            data_rows=DataRow.from_dict_list(json_dict.get("data_rows", [])),
        )


@dataclasses.dataclass(frozen=True)
class DatasetDataInfo(Formatter):
    data_hash: str
    title: str

    @classmethod
    def from_dict(cls, json_dict: Dict) -> DatasetDataInfo:
        return DatasetDataInfo(json_dict["data_hash"], json_dict["title"])


@dataclasses.dataclass(frozen=True)
class AddPrivateDataResponse(Formatter):
    """Response of add_private_data_to_dataset"""

    dataset_data_list: List[DatasetDataInfo]

    @classmethod
    def from_dict(cls, json_dict: Dict) -> AddPrivateDataResponse:
        data_info = json_dict["dataset_data_info"]
        dataset_data_info_list = []
        for mapping in data_info:
            dataset_data_info_list.append(DatasetDataInfo.from_dict(mapping))
        return AddPrivateDataResponse(dataset_data_info_list)


@dataclasses.dataclass(frozen=True)
class DatasetAPIKey(Formatter):
    dataset_hash: str
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


class CreateDatasetResponse(dict, Formatter):
    def __init__(
        self,
        title: str,
        storage_location: int,
        dataset_hash: str,
        user_hash: str,
    ):
        """
        This class has dict-style accessors for backwards compatibility.
        Clients who are using this class for the first time are encouraged to use the property accessors and setters
        instead of the underlying dictionary.
        The mixed use of the `dict` style member functions and the property accessors and setters is discouraged.

        WARNING: Do NOT use the `.data` member of this class. Its usage could corrupt the correctness of the
        datastructure.
        """

        super().__init__(
            {
                "title": title,
                "type": storage_location,
                "dataset_hash": dataset_hash,
                "user_hash": user_hash,
            }
        )

    @property
    def title(self) -> str:
        return self["title"]

    @title.setter
    def title(self, value: str) -> None:
        self["title"] = value

    @property
    def storage_location(self) -> StorageLocation:
        return StorageLocation(self["type"])

    @storage_location.setter
    def storage_location(self, value: StorageLocation) -> None:
        self["type"] = value.value

    @property
    def dataset_hash(self) -> str:
        return self["dataset_hash"]

    @dataset_hash.setter
    def dataset_hash(self, value: str) -> None:
        self["dataset_hash"] = value

    @property
    def user_hash(self) -> str:
        return self["user_hash"]

    @user_hash.setter
    def user_hash(self, value: str) -> None:
        self["user_hash"] = value

    @classmethod
    def from_dict(cls, json_dict: Dict) -> CreateDatasetResponse:
        return CreateDatasetResponse(
            title=json_dict["title"],
            storage_location=json_dict["type"],
            dataset_hash=json_dict["dataset_hash"],
            user_hash=json_dict["user_hash"],
        )


class StorageLocation(IntEnum):
    CORD_STORAGE = (0,)
    AWS = (1,)
    GCP = (2,)
    AZURE = 3
    OTC = 4

    @staticmethod
    def from_str(string_location: str) -> StorageLocation:
        return STORAGE_LOCATION_BY_STR[string_location]

    def get_str(self) -> str:
        if self == StorageLocation.CORD_STORAGE:
            return "CORD_STORAGE"
        elif self == StorageLocation.AWS:
            return "AWS_S3"
        elif self == StorageLocation.GCP:
            return "GCP_STR"
        elif self == StorageLocation.AZURE:
            return "AZURE_STR"
        elif self == StorageLocation.OTC:
            return "OTC_STR"


STORAGE_LOCATION_BY_STR: Dict[str, StorageLocation] = {location.get_str(): location for location in StorageLocation}

DatasetType = StorageLocation
"""For backwards compatibility"""


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


class SignedDicomURL(base_orm.BaseORM):
    """A signed URL object with supporting information."""

    DB_FIELDS = OrderedDict([("signed_url", str), ("data_hash", str), ("title", str), ("file_link", str)])


class SignedDicomsURL(base_orm.BaseListORM):
    """A signed URL object with supporting information."""

    BASE_ORM_TYPE = SignedDicomURL


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


class SingleImage(Image):
    """For native single image upload."""

    success: bool


@dataclasses.dataclass(frozen=True)
class Images:
    """Uploading multiple images in a batch mode."""

    success: bool


@dataclasses.dataclass(frozen=True)
class DicomSeries:
    data_hash: str
    title: str


@dataclasses.dataclass(frozen=True)
class ImageGroupOCR:
    processed_texts: Dict


@dataclasses.dataclass(frozen=True)
class ReEncodeVideoTaskResult:
    data_hash: str
    # The signed url is only present when using StorageLocation.CORD_STORAGE
    signed_url: Optional[str]
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
                ReEncodeVideoTaskResult(result["data_hash"], result.get("signed_url"), result["bucket_path"])
                for result in dict_results
            ]
            return ReEncodeVideoTask(json_dict["status"], results)
        else:
            return ReEncodeVideoTask(json_dict["status"])


@dataclasses.dataclass
class DatasetAccessSettings:
    """Settings for using the dataset object."""

    fetch_client_metadata: bool
    """Whether client metadata should be retrieved for each `data_row`."""


DEFAULT_DATASET_ACCESS_SETTINGS = DatasetAccessSettings(
    fetch_client_metadata=False,
)
