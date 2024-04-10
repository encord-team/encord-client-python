from datetime import datetime
from enum import auto
from typing import Dict, List, Optional
from uuid import UUID

from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO, Field
from encord.orm.dataset import LongPollingStatus

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore[assignment]


class StorageItemType(CamelStrEnum):
    VIDEO = auto()
    IMAGE = auto()
    IMAGE_GROUP = auto()
    IMAGE_SEQUENCE = auto()
    DICOM_FILE = auto()
    DICOM_SERIES = auto()


class StorageUserRole(CamelStrEnum):
    USER = auto()
    ADMIN = auto()


class StorageFolder(BaseDTO):
    uuid: UUID
    parent: Optional[UUID]
    name: str
    description: str
    client_metadata: Optional[str]
    owner: str
    created_at: datetime
    last_edited_at: datetime
    user_role: StorageUserRole
    synced_dataset_hash: Optional[UUID]


class CreateStorageFolderPayload(BaseDTO):
    name: str
    description: Optional[str]
    parent: Optional[UUID]
    client_metadata: Optional[str]


class UploadSignedUrlsPayload(BaseDTO):
    item_type: StorageItemType
    count: int
    frames_subfolder_name: Optional[str]


class UploadSignedUrl(BaseDTO):
    item_uuid: UUID
    object_key: str
    signed_url: str


class StorageItemWithName(BaseDTO):
    item_uuid: UUID
    name: str


class UploadLongPollingState(BaseDTO):
    """
    Response of the upload job's long polling request.

    Note: An upload job consists of job units, where job unit could be
    either a video, image group, dicom series, or a single image.
    """

    status: LongPollingStatus
    """Status of the upload job. Documented in detail in :meth:`encord.orm.dataset.LongPollingStatus`"""

    items_with_names: List[StorageItemWithName]
    """Information about data which was added to the folder."""

    errors: List[str]
    """Stringified list of exceptions."""

    units_pending_count: int
    """Number of upload job units that have pending status."""

    units_done_count: int
    """Number of upload job units that have done status."""

    units_error_count: int
    """Number of upload job units that have error status."""


class CustomerProvidedVideoMetadata(BaseDTO):
    """
    Media metadata for a video file; if provided, Encord service will skip frame synchronisation checks
    and will use the values specified here to render the video in the label editor.
    """

    fps: float
    duration: float
    width: int
    height: int
    file_size: int
    mime_type: str


class DataUploadImage(BaseDTO):
    object_url: str
    title: Optional[str] = None
    client_metadata: Dict = Field(default_factory=dict)
    external_file_type: Literal["IMAGE"] = "IMAGE"

    placeholder_item_uuid: Optional[UUID] = None


class DataUploadVideo(BaseDTO):
    object_url: str
    title: Optional[str] = None
    client_metadata: Dict = Field(default_factory=dict)

    external_file_type: Literal["VIDEO"] = "VIDEO"
    video_metadata: Optional[CustomerProvidedVideoMetadata] = None

    placeholder_item_uuid: Optional[UUID] = None


class DataUploadImageGroupImage(BaseDTO):
    url: str
    title: Optional[str]

    placeholder_item_uuid: Optional[UUID] = None


class DataUploadImageGroup(BaseDTO):
    images: List[DataUploadImageGroupImage]
    title: Optional[str]
    client_metadata: Dict = Field(default_factory=dict)
    create_video: bool = False

    external_file_type: Literal["IMG_GROUP"] = "IMG_GROUP"
    cluster_by_resolution: bool = False


class DataUploadImageGroupFromItems(BaseDTO):
    image_items: List[UUID]
    title: Optional[str]
    client_metadata: Dict = Field(default_factory=dict)
    create_video: bool
    video_url_prefix: Optional[str] = None

    external_file_type: Literal["IMG_GROUP_FROM_ITEMS"] = "IMG_GROUP_FROM_ITEMS"
    cluster_by_resolution: bool = False


class DataUploadDicomSeriesDicomFile(BaseDTO):
    url: str
    title: Optional[str]

    placeholder_item_uuid: Optional[UUID] = None


class DataUploadDicomSeries(BaseDTO):
    dicom_files: List[DataUploadDicomSeriesDicomFile]
    title: Optional[str]
    client_metadata: Dict = Field(default_factory=dict)

    external_file_type: Literal["DICOM"] = "DICOM"


class DataUploadItems(BaseDTO):
    videos: List[DataUploadVideo] = Field(default_factory=list)
    image_groups: List[DataUploadImageGroup] = Field(default_factory=list)
    dicom_series: List[DataUploadDicomSeries] = Field(default_factory=list)
    images: List[DataUploadImage] = Field(default_factory=list)
    image_groups_from_items: List[DataUploadImageGroupFromItems] = Field(default_factory=list)
    skip_duplicate_urls: bool = False


class PostUploadJobParams(BaseDTO):
    data_items: Optional[DataUploadItems] = None
    external_files: Optional[dict] = None
    integration_hash: Optional[UUID] = None
    ignore_errors: bool = False


class GetUploadJobParams(BaseDTO):
    timeout_seconds: int = 60
