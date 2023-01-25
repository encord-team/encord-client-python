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

import dataclasses
import json
import re
from collections import OrderedDict
from datetime import datetime
from enum import Enum, IntEnum
from typing import Dict, List, Optional
from uuid import UUID

from dateutil import parser

from encord.constants.enums import DataType
from encord.exceptions import EncordException
from encord.orm import base_orm
from encord.orm.formatter import Formatter

DATETIME_STRING_FORMAT = "%Y-%m-%d %H:%M:%S"


class DatasetUserRole(IntEnum):
    ADMIN = 0
    USER = 1


@dataclasses.dataclass(frozen=True)
class DatasetUser(Formatter):
    user_email: str
    user_role: DatasetUserRole
    dataset_hash: str

    @classmethod
    def from_dict(cls, json_dict: Dict):
        return DatasetUser(
            user_email=json_dict["user_email"],
            user_role=DatasetUserRole(json_dict["user_role"]),
            dataset_hash=json_dict["dataset_hash"],
        )


class DatasetUsers:
    pass


@dataclasses.dataclass(frozen=True)
class DataClientMetadata:
    payload: dict


@dataclasses.dataclass(frozen=True)
class SignedUrl:
    signed_url: str


@dataclasses.dataclass(frozen=True)
class ImageData:
    id: int
    title: str
    user_hash: UUID
    file_link: str
    signed_url: str
    file_type: str
    file_size: float
    image_hash: UUID
    storage_location: StorageLocation
    created_at: datetime
    last_edited_at: datetime
    height: int
    width: int

    @classmethod
    def from_dict(cls, json_dict: Dict):
        return ImageData(
            id=json_dict["id"],
            user_hash=json_dict["user_hash"],
            title=json_dict["title"],
            file_link=json_dict["file_link"],
            file_type=json_dict["file_type"],
            file_size=json_dict["file_size"],
            image_hash=json_dict["image_hash"],
            storage_location=json_dict["storage_location"],
            created_at=parser.parse(json_dict["created_at"]),
            last_edited_at=parser.parse(json_dict["last_edited_at"]),
            height=json_dict["height"],
            width=json_dict["width"],
        )


@dataclasses.dataclass(frozen=True)
class ImagesInGroup:
    images: List[Dict]


@dataclasses.dataclass(frozen=True)
class DicomFileLinks:
    file_links: List[str]


def is_signed_url(string: str) -> bool:
    pattern = re.compile(r"^https://.*")
    return pattern.match(string) is not None


def check_if_images_have_signed_url(images: List[ImageData]) -> bool:
    if len(images) == 0:
        return False
    return is_signed_url(images[0].file_link)


def check_if_file_links_are_signed_urls(file_links: List[str]) -> bool:
    if len(file_links) == 0:
        return False
    return is_signed_url(file_links[0])


class DataRow(dict, Formatter):
    def __init__(
        self,
        uid: str,
        title: str,
        data_type: DataType,
        created_at: datetime,
        last_edited_at: datetime,
        width: int,
        height: int,
        file_link: str,
        file_size: int,
        file_type: str,
        storage_location: StorageLocation,
        client_metadata: Optional[dict],
        frames_per_second: Optional[int],
        duration: Optional[int],
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
                "last_edited_at": last_edited_at.strftime(DATETIME_STRING_FORMAT),
                "width": width,
                "height": height,
                "file_link": file_link,
                "file_size": file_size,
                "file_type": file_type,
                "storage_location": storage_location,
                "frames_per_second": frames_per_second,
                "duration": duration,
                "client_metadata": client_metadata,
                "_querier": None,
                "images": None,
                "signed_url": None,
                "dicom_file_links": None,
            }
        )

    @property
    def uid(self) -> str:
        return self["data_hash"]

    @property
    def title(self) -> str:
        return self["data_title"]

    @title.setter
    def title(self, value: str) -> None:
        self["data_title"] = value

    @property
    def data_type(self) -> DataType:
        return DataType.from_upper_case_string(self["data_type"])

    @property
    def created_at(self) -> datetime:
        return parser.parse(self["created_at"])

    @property
    def frames_per_second(self) -> Optional[int]:
        """
        Returns:
        If the data type is `DataType.VIDEO` this returns the actual number of frames per second for the video.
        Otherwise, it returns None as a `frames_per_second` field is not applicable.
        """
        if self.data_type != DataType.VIDEO:
            return None
        return self["frames_per_second"]

    @property
    def duration(self) -> Optional[int]:
        """
        Returns:
        If the data type is `DataType.VIDEO` this returns the actual video duration.
        Otherwise, it returns None as a `duration` field is not applicable.
        """
        if self.data_type != DataType.VIDEO:
            return None
        return self["duration"]

    @property
    def client_metadata(self) -> Optional[dict]:
        """
        DEPRECATED - please use `get_client_metadata` instead.
        Returns:
        If `client_metadata` is disabled via the :class:`encord.orm.dataset.DatasetAccessSettings
        then this returns `null`.
        Otherwise, this returns custom client metadata.
        """
        if self["client_metadata"] is None:
            if self["_querier"] is not None:
                res = self["_querier"].basic_getter(DataClientMetadata, uid=self.uid)
                self["client_metadata"] = res.payload
            else:
                raise EncordException(f"Could not retrieve client metadata for DataRow with uid: {self.uid}")
        return self["client_metadata"]

    @client_metadata.setter
    def client_metadata(self, new_client_metadata: [Dict, List, int, float, bool, str]) -> None:
        """
        DEPRECATED - please use `set_client_metadata` instead.
        This updates custom client metadata with the new given data.
        """
        if self["_querier"] is not None:
            res = self["_querier"].basic_setter(
                DataClientMetadata,
                uid=self.uid,
                payload={"new_client_metadata": new_client_metadata},
            )
            if res:
                self["client_metadata"] = new_client_metadata
            else:
                raise EncordException(f"Could not update client metadata for DataRow with uid: {self.uid}")

    def get_client_metadata(self):
        """
        Returns:
        If `client_metadata` is disabled via the :class:`encord.orm.dataset.DatasetAccessSettings
        then this returns `null`.
        Otherwise, this returns custom client metadata.
        """
        return self.client_metadata

    def set_client_metadata(self, new_client_metadata: [Dict, List, int, float, bool, str]) -> None:
        """
        DEPRECATED - please use `set_client_metadata` instead.
        This method updates custom client metadata with the new given data.
        """
        self.client_metadata = new_client_metadata

    @property
    def width(self) -> int:
        """
        Returns:
        This returns an actual width of the data asset.
        """
        return self["width"]

    @property
    def height(self) -> int:
        """
        Returns:
        This returns an actual height of the data asset.
        """
        return self["height"]

    @property
    def last_edited_at(self) -> datetime:
        """
        Returns:
        This returns a datetime when the given data asset was last edited.
        """
        return parser.parse(self["last_edited_at"])

    @property
    def file_link(self) -> str:
        """
        Returns:
        This returns a permanent file link of the given data asset.
        If the data type is `DataType.DICOM` then this returns an empty string.
        """
        return self["file_link"]

    def get_signed_url(self):
        """
        Returns:
        This returns a generated cached signed url link of the given data asset.
        """
        if self.data_type in [DataType.VIDEO, DataType.IMG_GROUP, DataType.IMAGE] and self["signed_url"] is None:
            if self["_querier"] is not None:
                payload = {"data_type": self.data_type.value}
                res = self["_querier"].basic_getter(SignedUrl, uid=self.uid, payload=payload)
                self["signed_url"] = res.signed_url
            else:
                raise EncordException(
                    f"Could not get signed url for DataRow with uid: {self.uid}."
                    f"This could be because the given DataRow was initialised incorrectly."
                )
        return self["signed_url"]

    @property
    def file_size(self) -> int:
        """
        Returns:
        This returns an actual file size of the given data asset.
        """
        return self["file_size"]

    @property
    def file_type(self) -> str:
        """
        Returns:
        This returns a MIME file type of the given data asset.
        """
        return self["file_type"]

    @property
    def storage_location(self) -> StorageLocation:
        """
        Returns:
        This returns a storage location of the given data asset.
        The returned type is `StorageLocation`.
        """
        return self["storage_location"]

    def get_images(self, get_signed_url: bool = False) -> List[ImageData]:
        """
        Args:
            get_signed_url: optional flag which is responsible for generating signed urls for returned
            images data (`False` by default)
        Returns:
            This method lazily retrieves list of images, cache and returns it for the given DataRow image group.
            If the data type is not `DataType.IMG_GROUP` then this method simply returns `None`.
            If `get_signed_url` is `False` then `signed_url' of each image data in the returned array is None.
            Otherwise, `signed_url` for each image is a generated signed url link.
        """
        if self.data_type == DataType.IMG_GROUP:
            if self["_querier"] is not None:
                if self["images"] is None or get_signed_url != check_if_images_have_signed_url(self["images"]):
                    payload = {
                        "get_signed_url": get_signed_url,
                    }
                    res = self["_querier"].basic_getter(ImagesInGroup, uid=self.uid, payload=payload)
                    self["images"] = [ImageData.from_dict(image) for image in res.images]
            else:
                raise EncordException(
                    f"Could not get images data for image group with uid: {self.uid}. "
                    f"This could be because the given DataRow was initialised incorrectly."
                )
        return self["images"]

    def get_dicom_file_links(self, get_signed_url: bool = False) -> List[str]:
        """
        Args:
            get_signed_url: optional flag which is responsible for generating signed urls(`False` by default)
        Returns:
            This method lazily retrieves and returns list of file links for the given dicom DataRow and cache it.
            If the data type is not `DataType.DICOM` then this method simply returns `None`.
            If the `get_signed_url` is `True` then the method returns array of generated signed url file links.
            Otherwise, this returns permanent file links.
        """
        if self.data_type == DataType.DICOM:
            if self["_querier"] is not None:
                if self["dicom_file_links"] is None or get_signed_url != check_if_file_links_are_signed_urls(
                    self["dicom_file_links"]
                ):
                    payload = {
                        "get_signed_url": get_signed_url,
                    }
                    res = self["_querier"].basic_getter(DicomFileLinks, uid=self.uid, payload=payload)
                    self["dicom_file_links"] = res.file_links
            else:
                raise EncordException(
                    f"Could not get file links for dicom with uid: {self.uid}."
                    f"This could be because the given DataRow was initialised incorrectly."
                )
        return self["dicom_file_links"]

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
            last_edited_at=parser.parse(json_dict["last_edited_at"]),
            width=json_dict["width"],
            height=json_dict["height"],
            file_link=json_dict["file_link"],
            file_size=json_dict["file_size"],
            file_type=json_dict["file_type"],
            storage_location=json_dict["storage_location"],
            frames_per_second=json_dict["frames_per_second"],
            duration=json_dict["duration"],
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
class DicomDeidentifyTask:
    dicom_urls: List[str]
    integration_hash: str


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
