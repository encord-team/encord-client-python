from __future__ import annotations

import dataclasses
from collections import OrderedDict
from datetime import datetime
from enum import Enum, IntEnum, auto
from types import MappingProxyType
from typing import Any, Dict, List, Optional
from uuid import UUID

from encord.common.constants import DATETIME_STRING_FORMAT
from encord.common.deprecated import deprecated
from encord.common.time_parser import parse_datetime
from encord.constants.enums import DataType
from encord.exceptions import EncordException
from encord.orm import base_orm
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO
from encord.orm.formatter import Formatter
from encord.utilities.common import _get_dict_without_none_keys


class DatasetUserRole(IntEnum):
    ADMIN = 0
    USER = 1


class DatasetUserRoleV2(CamelStrEnum):
    ADMIN = auto()
    USER = auto()


def dataset_user_role_str_enum_to_int_enum(str_enum: DatasetUserRoleV2) -> DatasetUserRole:
    return {
        DatasetUserRoleV2.ADMIN: DatasetUserRole.ADMIN,
        DatasetUserRoleV2.USER: DatasetUserRole.USER,
    }[str_enum]


class DatasetUser(BaseDTO):
    user_email: str
    user_role: DatasetUserRole
    dataset_hash: str


class DatasetUsers:
    pass


class DataLinkDuplicatesBehavior(Enum):
    DUPLICATE = "DUPLICATE"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclasses.dataclass(frozen=True)
class DataClientMetadata:
    payload: dict


class ImageData:
    """Information about individual images within a single :class:`~encord.orm.dataset.DataRow` of type
    :meth:`DataType.IMG_GROUP <encord.constants.enums.DataType.IMG_GROUP>`. Get this information
    via the :meth:`DataRow.images <encord.orm.dataset.DataRow.images>` property.
    """

    def __init__(
        self,
        image_hash: UUID,
        title: str,
        file_link: str,
        file_type: str,
        file_size: int,
        storage_location: StorageLocation,
        created_at: datetime,
        last_edited_at: datetime,
        width: int,
        signed_url: Optional[str],
        height: int,
    ):
        self._image_hash = image_hash
        self._title = title
        self._file_link = file_link
        self._file_type = file_type
        self._file_size = file_size
        self._storage_location = storage_location
        self._created_at = created_at
        self._last_edited_at = last_edited_at
        self._height = height
        self._width = width
        self._signed_url = signed_url

    @property
    def image_hash(self) -> str:
        return str(self._image_hash)

    @property
    def title(self) -> str:
        return self._title

    @property
    def file_link(self) -> str:
        return self._file_link

    @property
    def file_type(self) -> str:
        """The MIME type of the file."""
        return self._file_type

    @property
    def file_size(self) -> int:
        """The size of the file in bytes."""
        return self._file_size

    @property
    def storage_location(self) -> StorageLocation:
        return self._storage_location

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def last_edited_at(self) -> datetime:
        return self._last_edited_at

    @property
    def height(self) -> int:
        return self._height

    @property
    def width(self) -> int:
        return self._width

    @property
    def signed_url(self) -> Optional[str]:
        """The signed URL if one was generated when this class was created."""
        return self._signed_url

    @classmethod
    def from_dict(cls, json_dict: Dict) -> ImageData:
        return ImageData(
            title=json_dict["title"],
            file_link=json_dict["file_link"],
            file_type=json_dict["file_type"],
            file_size=json_dict["file_size"],
            image_hash=json_dict["image_hash"],
            storage_location=json_dict["storage_location"],
            created_at=parse_datetime(json_dict["created_at"]),
            last_edited_at=parse_datetime(json_dict["last_edited_at"]),
            height=json_dict["height"],
            width=json_dict["width"],
            signed_url=json_dict.get("signed_url"),
        )

    @classmethod
    def from_list(cls, json_list: List) -> List[ImageData]:
        return [cls.from_dict(json_dict) for json_dict in json_list]

    def __repr__(self):
        return f"ImageData(title={self.title}, image_hash={self.image_hash})"


class DataRow(dict, Formatter):
    """Each individual DataRow is one upload of a video, image group, single image, or DICOM series.

    This class has dict-style accessors for backwards compatibility.
    Clients who are using this class for the first time are encouraged to use the property accessors and setters
    instead of the underlying dictionary.
    The mixed use of the `dict` style member functions and the property accessors and setters is discouraged.

    WARNING: Do NOT use the `.data` member of this class. Its usage could corrupt the correctness of the
    datastructure.
    """

    def __init__(
        self,
        uid: str,
        title: str,
        data_type: DataType,
        created_at: datetime,
        last_edited_at: datetime,
        width: Optional[int],
        height: Optional[int],
        file_link: Optional[str],
        file_size: Optional[int],
        file_type: Optional[str],
        storage_location: StorageLocation,
        client_metadata: Optional[dict],
        frames_per_second: Optional[int],
        duration: Optional[int],
        images_data: Optional[List[dict]],
        signed_url: Optional[str],
        is_optimised_image_group: Optional[bool],
        backing_item_uuid: Optional[UUID],
    ):
        parsed_images = None
        if images_data is not None:
            parsed_images = [ImageData.from_dict(image_data) for image_data in images_data]

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
                "images_data": parsed_images,
                "signed_url": signed_url,
                "is_optimised_image_group": is_optimised_image_group,
                "backing_item_uuid": backing_item_uuid,
                "_dirty_fields": [],
            }
        )

    @property
    def uid(self) -> str:
        """The unique identifier for this data row. Note that the setter does not update the data on the server."""
        return self["data_hash"]

    @uid.setter
    def uid(self, value: str) -> None:
        self["data_hash"] = value

    @property
    def title(self) -> str:
        """The data title.

        The setter updates the custom client metadata. This queues a request for the backend which will be
        executed on a call of :meth:`.DataRow.upload`.
        """
        return self["data_title"]

    @title.setter
    def title(self, value: str) -> None:
        self["_dirty_fields"].append("data_title")
        self["data_title"] = value

    @property
    def data_type(self) -> DataType:
        return DataType.from_upper_case_string(self["data_type"])

    @data_type.setter
    def data_type(self, value: DataType) -> None:
        """DEPRECATED. Do not this function as it will never update the created_at in the server."""
        self["data_type"] = value.to_upper_case_string()

    @property
    def created_at(self) -> datetime:
        return parse_datetime(self["created_at"])

    @created_at.setter
    def created_at(self, value: datetime) -> None:
        """DEPRECATED. Do not this function as it will never update the created_at in the server."""
        self["created_at"] = value.strftime(DATETIME_STRING_FORMAT)

    @property
    def frames_per_second(self) -> Optional[int]:
        """If the data type is :meth:`DataType.VIDEO <encord.constants.enums.DataType.VIDEO>` this returns the
        actual number of frames per second for the video. Otherwise, it returns `None` as a frames_per_second
        field is not applicable.
        """
        return self["frames_per_second"]

    @property
    def duration(self) -> Optional[int]:
        """If the data type is :meth:`DataType.VIDEO <encord.constants.enums.DataType.VIDEO>` this returns the
        actual duration for the video. Otherwise, it returns `None` as a duration field is not applicable.
        """
        if self.data_type != DataType.VIDEO:
            return None
        return self["duration"]

    @property
    def client_metadata(self) -> Optional[MappingProxyType]:
        """The currently cached client metadata. To cache the client metadata, use the
        :meth:`~encord.orm.dataset.DataRow.refetch_data()` function.

        The setter updates the custom client metadata. This queues a request for the backend which will
        be executed on a call of :meth:`.DataRow.upload`.
        """
        return MappingProxyType(self["client_metadata"]) if self["client_metadata"] is not None else None

    @client_metadata.setter
    def client_metadata(self, new_client_metadata: Dict) -> None:
        self["_dirty_fields"].append("client_metadata")
        self["client_metadata"] = new_client_metadata

    @property
    def width(self) -> Optional[int]:
        """An actual width of the data asset. This is `None` for data types of
        :meth:`DataType.IMG_GROUP <encord.constants.enums.DataType.IMG_GROUP>` where
        :meth:`is_image_sequence <encord.data.DataRow.is_image_sequence>` is `False`, because
        each image in this group can have a different dimension. Inspect the
        :meth:`images <encord.data.DataRow.images>` to get the height of individual images.
        """
        return self["width"]

    @property
    def height(self) -> Optional[int]:
        """An actual height of the data asset. This is `None` for data types of
        :meth:`DataType.IMG_GROUP <encord.constants.enums.DataType.IMG_GROUP>` where
        :meth:`is_image_sequence <encord.data.DataRow.is_image_sequence>` is `False`, because
        each image in this group can have a different dimension. Inspect the
        :meth:`images <encord.data.DataRow.images>` to get the height of individual images.
        """
        return self["height"]

    @property
    def last_edited_at(self) -> datetime:
        return parse_datetime(self["last_edited_at"])

    @property
    def file_link(self) -> Optional[str]:
        """A permanent file link of the given data asset. When stored in
        :meth:`StorageLocation.CORD_STORAGE <encord.orm.dataset.StorageLocation.CORD_STORAGE>` this will be the
        internal file path. In private bucket storage location this will be the full path to the file.
        If the data type is `DataType.DICOM` then this returns None as no single file is associated with the
        series.
        """
        return self["file_link"]

    @property
    def signed_url(self) -> Optional[str]:
        """The cached signed url of the given data asset. To cache the signed url, use the
        :meth:`~encord.orm.dataset.DataRow.refetch_data()` function.
        """
        return self["signed_url"]

    @property
    def file_size(self) -> int:
        """The file size of the given data asset in bytes."""
        return self["file_size"]

    @property
    def file_type(self) -> str:
        """A MIME file type of the given data asset as a string"""
        return self["file_type"]

    @property
    def storage_location(self) -> StorageLocation:
        return self["storage_location"]

    @property
    def images_data(self) -> Optional[List[ImageData]]:
        """A list of the cached :class:`~encord.orm.dataset.ImageData` objects for the given data asset.
        Fetch the images with appropriate settings in the :meth:`~encord.orm.dataset.DataRow.refetch_data()` function.
        If the data type is not :meth:`DataType.IMG_GROUP <encord.constants.enums.DataType.IMG_GROUP>`
        then this returns None.
        """
        return self["images_data"]

    @property
    @deprecated("0.1.98", ".is_image_sequence")
    def is_optimised_image_group(self) -> Optional[bool]:
        """If the data type is an :meth:`DataType.IMG_GROUP <encord.constants.enums.DataType.IMG_GROUP>`,
        returns whether this is a performance optimised image group. Returns `None` for other data types.

        DEPRECATED: This method is deprecated and will be removed in the upcoming library version.
        Please use :meth:`.is_image_sequence` instead
        """
        return self.is_image_sequence

    @property
    def is_image_sequence(self) -> Optional[bool]:
        """If the data type is an :meth:`DataType.IMG_GROUP <encord.constants.enums.DataType.IMG_GROUP>`,
        returns whether this is an image sequence. Returns `None` for other data types.

        For more details refer to the
        :ref:`documentation on image sequences <https://docs.encord.com/docs/annotate-supported-data#image-sequences>`
        """
        return self["is_optimised_image_group"]

    @property
    def backing_item_uuid(self) -> UUID:
        """The id of the :class:`encord.storage.StorageItem` that underlies this data row.
        See also :meth:`encord.user_client.EncordUserClient.get_storage_item`.
        """
        backing_item_uuid: Optional[UUID] = self.get("backing_item_uuid")
        if not backing_item_uuid:
            raise NotImplementedError("Storage API is not yet implemented by the service")
        return backing_item_uuid

    def refetch_data(
        self,
        *,
        signed_url: bool = False,
        images_data_fetch_options: Optional[ImagesDataFetchOptions] = None,
        client_metadata: bool = False,
    ):
        """Fetches all the most up-to-date data. If any of the parameters are falsy, the current values will not be
        updated.

        Args:
            signed_url: If True, this will fetch a generated signed url of the data asset.
            images_data_fetch_options: If not None, this will fetch the image data of the data asset. You can
                additionally specify what to fetch with the :class:`.ImagesDataFetchOptions` class.
            client_metadata: If True, this will fetch the client metadata of the data asset.
        """
        if self["_querier"] is not None:
            if images_data_fetch_options is not None:
                images_data_fetch_options_dict = dataclasses.asdict(images_data_fetch_options)
            else:
                images_data_fetch_options_dict = None

            payload = {
                "additional_data": {
                    "signed_url": signed_url,
                    "images_data_fetch_options": images_data_fetch_options_dict,
                    "client_metadata": client_metadata,
                }
            }
            res = self["_querier"].basic_getter(DataRow, uid=self.uid, payload=payload)
            self._update_current_class(res)

        else:
            raise EncordException("Could not fetch data. The DataRow is in an invalid state.")

    def save(self) -> None:
        """Sync local state to the server, if updates are made. This is a blocking function.

        The newest values from the Encord server will update the current :class:`.DataRow` object.
        """
        if self["_querier"] is not None:
            payload = {}
            for dirty_field in self["_dirty_fields"]:
                payload[dirty_field] = self[dirty_field]
            self["_dirty_fields"] = []

            res = self["_querier"].basic_setter(DataRow, uid=self.uid, payload=payload)
            if res:
                self._compare_upload_payload(res, payload)
                data_row_dict = res["data_row"]
                self._update_current_class(DataRow.from_dict(data_row_dict))
            else:
                raise EncordException(f"Could not upload data for DataRow with uid: {self.uid}")
        else:
            raise EncordException("Could not upload data. The DataRow is in an invalid state.")

    @classmethod
    def from_dict(cls, json_dict: Dict) -> DataRow:
        data_type = DataType.from_upper_case_string(json_dict["data_type"])
        backing_item_uuid_value = json_dict.get("backing_item_uuid")
        backing_item_uuid = UUID(backing_item_uuid_value) if backing_item_uuid_value else None

        return DataRow(
            uid=json_dict["data_hash"],
            title=json_dict["data_title"],
            # The API server currently returns upper-cased DataType strings.
            data_type=data_type,
            created_at=parse_datetime(json_dict["created_at"]),
            client_metadata=json_dict.get("client_metadata"),
            last_edited_at=parse_datetime(json_dict["last_edited_at"]),
            width=json_dict["width"],
            height=json_dict["height"],
            file_link=json_dict["file_link"],
            file_size=json_dict["file_size"],
            file_type=json_dict["file_type"],
            storage_location=StorageLocation(json_dict["storage_location"]),
            frames_per_second=json_dict["frames_per_second"],
            duration=json_dict["duration"],
            signed_url=json_dict.get("signed_url"),
            is_optimised_image_group=json_dict.get("is_optimised_image_group"),
            backing_item_uuid=backing_item_uuid,
            images_data=json_dict.get("images_data"),
        )

    @classmethod
    def from_dict_list(cls, json_list: List) -> List[DataRow]:
        ret: List[DataRow] = list()
        for json_dict in json_list:
            ret.append(cls.from_dict(json_dict))
        return ret

    def _compare_upload_payload(self, upload_res: dict, initial_payload: dict) -> None:
        """Compares the upload payload with the response from the server.

        NOTE: this could also compare the new fields, field by field and update the current DataRow.
        """
        updated_fields = set(upload_res["updated_fields"])
        fields_requested_for_update = set(initial_payload.keys())
        if updated_fields != fields_requested_for_update:
            raise EncordException(
                f"The actually updated fields `{updated_fields}` do not match the fields that are requested for update."
            )

    def _update_current_class(self, new_class: DataRow) -> None:
        res_dict = _get_dict_without_none_keys(dict(new_class))
        self.update(res_dict)


@dataclasses.dataclass(frozen=True)
class DataRows(dict, Formatter):
    """This is a helper class that forms request for filtered dataset rows
    Not intended to be used directly
    """

    def __init__(self, data_rows: List[DataRow]):
        super().__init__(
            {
                "data_rows": data_rows,
            }
        )

    @classmethod
    def from_dict(cls, json_dict: Dict) -> DataRow:  # type: ignore[override]
        return DataRow.from_dict(json_dict)


@dataclasses.dataclass(frozen=True)
class DatasetInfo:
    """This class represents a dataset in the context of listing"""

    dataset_hash: str
    user_hash: str
    title: str
    description: str
    type: int
    created_at: datetime
    last_edited_at: datetime
    backing_folder_uuid: Optional[UUID] = None


class Dataset(dict, Formatter):
    def __init__(
        self,
        title: str,
        storage_location: str,
        data_rows: List[DataRow],
        dataset_hash: str,
        description: Optional[str] = None,
        backing_folder_uuid: Optional[UUID] = None,
    ):
        """DEPRECATED - prefer using the :class:`encord.dataset.Dataset` class instead.

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
                "backing_folder_uuid": backing_folder_uuid,
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

    @property
    def backing_folder_uuid(self) -> Optional[UUID]:
        return self["backing_folder_uuid"]

    @backing_folder_uuid.setter
    def backing_folder_uuid(self, value: Optional[UUID]) -> None:
        self["backing_folder_uuid"] = value

    @classmethod
    def from_dict(cls, json_dict: Dict) -> Dataset:
        backing_folder_uuid_value = json_dict.get("backing_folder_uuid")

        return Dataset(
            title=json_dict["title"],
            description=json_dict["description"],
            storage_location=json_dict["dataset_type"],
            dataset_hash=json_dict["dataset_hash"],
            backing_folder_uuid=UUID(backing_folder_uuid_value) if backing_folder_uuid_value else None,
            data_rows=DataRow.from_dict_list(json_dict.get("data_rows", [])),
        )


class DatasetDataInfo(BaseDTO):
    data_hash: str
    title: str
    backing_item_uuid: UUID


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


class CreateDatasetResponse(dict, Formatter):
    def __init__(
        self,
        title: str,
        storage_location: int,
        dataset_hash: str,
        user_hash: str,
        backing_folder_uuid: Optional[UUID],
    ):
        """This class has dict-style accessors for backwards compatibility.
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
                "backing_folder_uuid": backing_folder_uuid,
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

    @property
    def backing_folder_uuid(self) -> Optional[UUID]:
        return self["backing_folder_uuid"]

    @backing_folder_uuid.setter
    def backing_folder_uuid(self, value: Optional[UUID]) -> None:
        self["backing_folder_uuid"] = value

    @classmethod
    def from_dict(cls, json_dict: Dict) -> CreateDatasetResponse:
        backing_folder_uuid_value = json_dict.get("backing_folder_uuid")
        return CreateDatasetResponse(
            title=json_dict["title"],
            storage_location=json_dict["type"],
            dataset_hash=json_dict["dataset_hash"],
            user_hash=json_dict["user_hash"],
            backing_folder_uuid=UUID(backing_folder_uuid_value) if backing_folder_uuid_value else None,
        )


class StorageLocation(IntEnum):
    CORD_STORAGE = (0,)
    AWS = (1,)
    GCP = (2,)
    AZURE = 3
    S3_COMPATIBLE = 4

    NEW_STORAGE = -99
    """
    This is a placeholder for a new storage location that is not yet supported by your SDK version.
    Please update your SDK to the latest version.
    """

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
        elif self == StorageLocation.S3_COMPATIBLE:
            return "S3_COMPATIBLE_STR"
        else:
            return "NEW_STORAGE"

    @classmethod
    def _missing_(cls, value: Any) -> StorageLocation:
        return StorageLocation.NEW_STORAGE


STORAGE_LOCATION_BY_STR: Dict[str, StorageLocation] = {location.get_str(): location for location in StorageLocation}

DatasetType = StorageLocation
"""For backwards compatibility"""


class DatasetData(base_orm.BaseORM):
    """Video base ORM."""

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


class SignedAudioURL(base_orm.BaseORM):
    """A signed URL object with supporting information."""

    DB_FIELDS = OrderedDict([("signed_url", str), ("data_hash", str), ("title", str), ("file_link", str)])


class SignedDicomURL(base_orm.BaseORM):
    """A signed URL object with supporting information."""

    DB_FIELDS = OrderedDict([("signed_url", str), ("data_hash", str), ("title", str), ("file_link", str)])


class SignedDicomsURL(base_orm.BaseListORM):
    """A signed URL object with supporting information."""

    BASE_ORM_TYPE = SignedDicomURL


class Video(base_orm.BaseORM):
    """A video object with supporting information."""

    DB_FIELDS = OrderedDict([("data_hash", str), ("title", str), ("file_link", str), ("backing_item_uuid", UUID)])

    NON_UPDATABLE_FIELDS = {
        "data_hash",
        "backing_item_uuid",
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
            ("image_hash", str),
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


class Audio(base_orm.BaseORM):
    """An audio object with supporting information."""

    DB_FIELDS = OrderedDict([("data_hash", str), ("title", str), ("file_link", str), ("backing_item_uuid", UUID)])

    NON_UPDATABLE_FIELDS = {
        "data_hash",
        "backing_item_uuid",
    }


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


class ReEncodeVideoTaskResult(BaseDTO):
    data_hash: str
    # The signed url is only present when using StorageLocation.CORD_STORAGE
    signed_url: Optional[str]
    bucket_path: str


class ReEncodeVideoTask(BaseDTO):
    """A re encode video object with supporting information."""

    status: str
    result: Optional[List[ReEncodeVideoTaskResult]] = None


@dataclasses.dataclass
class DatasetAccessSettings:
    """Settings for using the dataset object."""

    fetch_client_metadata: bool
    """Whether client metadata should be retrieved for each `data_row`."""


DEFAULT_DATASET_ACCESS_SETTINGS = DatasetAccessSettings(
    fetch_client_metadata=False,
)


@dataclasses.dataclass
class ImagesDataFetchOptions:
    fetch_signed_urls: bool = False
    """
    Whether to fetch signed urls for each individual image. Only set this to true if you need to download the
    images.
    """


class LongPollingStatus(str, Enum):
    PENDING = "PENDING"
    """Job will automatically start soon (waiting in queue) or already started processing."""

    DONE = "DONE"
    """
    Job has finished successfully (possibly with errors if `ignore_errors=True`).

    If `ignore_errors=False` was specified in :meth:`encord.dataset.Dataset.add_private_data_to_dataset_start,
    the job will only have the status `DONE` if there were no errors.

    If `ignore_errors=True` was specified in :meth:`encord.dataset.Dataset.add_private_data_to_dataset_start`,
    the job will always show the status `DONE` once complete and will never show `ERROR`
    status if this flag was set to `True`. There could be errors that were ignored.

    Information about number of errors and stringified exceptions is available in the
    `units_error_count: int` and `errors: List[str]` attributes.
    """

    ERROR = "ERROR"
    """
    Job has completed with errors. This can only happen if `ignore_errors` was set to `False`.
    Information about errors is available in the `units_error_count: int` and `errors: List[str]` attributes.
    """

    CANCELLED = "CANCELLED"
    """
    Job was cancelled explicitly by the user through the Encord UI or via the Encord SDK using the
    `add_data_to_folder_job_cancel` method.

    In the context of this status:
    - The job may have been partially processed, but it was explicitly interrupted before completion
      by a user action.
    - Cancellation can occur either manually through the Encord UI or programmatically using the SDK
      method `add_data_to_folder_job_cancel`.
    - Once a job is cancelled, no further processing will occur, and any processed data before the
      cancellation will be available.
    - The presence of cancelled data units (`units_cancelled_count`) indicates that some data upload
      units were interrupted and cancelled before completion.
    - If `ignore_errors` was set to `True`, the job may continue despite errors, and cancellation will
      only apply to the unprocessed units.
    """


class DataUnitError(BaseDTO):
    """A description of an error for an individual upload item"""

    object_urls: List[str]
    """URLs involved. A single item for videos and images; a list of frames for image groups and DICOM"""

    error: str
    """The error message"""

    subtask_uuid: UUID
    """Opaque ID of the process. Please quote this when contacting Encord support."""

    action_description: str
    """Human-readable description of the action that failed (e.g. 'Uploading DICOM series')."""


class DatasetDataLongPolling(BaseDTO):
    """Response of the upload job's long polling request.

    Note: An upload job consists of job units, where job unit could be
    either a video, image group, dicom series, or a single image.
    """

    status: LongPollingStatus
    """Status of the upload job. Documented in detail in :meth:`LongPollingStatus`"""

    data_hashes_with_titles: List[DatasetDataInfo]
    """Information about data which was added to the dataset."""

    errors: List[str]
    """Stringified list of exceptions."""

    data_unit_errors: List[DataUnitError]
    """Structured list of per-item upload errors. See :class:`DataUnitError` for more details."""

    units_pending_count: int
    """Number of upload job units that have pending status."""

    units_done_count: int
    """Number of upload job units that have done status."""

    units_error_count: int
    """Number of upload job units that have error status."""

    units_cancelled_count: int
    """Number of upload job units that have been cancelled."""


@dataclasses.dataclass(frozen=True)
class DatasetLinkItems:
    pass


class CreateDatasetPayload(BaseDTO):
    title: str
    description: Optional[str]

    create_backing_folder: bool  # this creates a legacy "mirror" dataset and it's backing folder in one go

    # only for analytics, to know if customers are
    # using depreciated EncordUserClient.create_private_dataset
    # this is only place which should pass legacy_call=True
    legacy_call: bool  # this field will be removed soon


class CreateDatasetResponseV2(BaseDTO):
    dataset_uuid: UUID
    backing_folder_uuid: Optional[UUID] = None  # a 'not None' indicates a legacy "mirror" dataset was created


class DatasetsWithUserRolesListParams(BaseDTO):
    title_eq: Optional[str]
    title_like: Optional[str]
    description_eq: Optional[str]
    description_like: Optional[str]
    created_before: Optional[datetime]
    created_after: Optional[datetime]
    edited_before: Optional[datetime]
    edited_after: Optional[datetime]
    include_org_access: Optional[bool] = False


class DatasetWithUserRole(BaseDTO):
    dataset_uuid: UUID
    title: str
    description: str
    created_at: datetime
    last_edited_at: datetime
    user_role: Optional[DatasetUserRoleV2]

    storage_location: Optional[StorageLocation] = None  # legacy field: you can have data from mixed locations now
    backing_folder_uuid: Optional[UUID] = None  # if set, this indicates a legacy 'mirror' dataset


class DatasetsWithUserRolesListResponse(BaseDTO):
    result: List[DatasetWithUserRole]
