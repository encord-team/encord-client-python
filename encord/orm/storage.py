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


class StorageLocationName(CamelStrEnum):
    ENCORD = auto()
    GCP = auto()
    S3 = auto()
    AZURE = auto()
    OPEN_TELEKOM = auto()
    DIRECT_ACCESS = auto()


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


class StorageItem(BaseDTO):
    uuid: UUID
    parent: UUID
    item_type: StorageItemType
    name: str
    description: str
    client_metadata: str
    owner: str
    created_at: datetime
    last_edited_at: datetime
    is_tombstone: bool = False
    """This item has been deleted but the link is retained for consistency reasons.
    Mostly for items in the 'cloud linked folders' that are referenced but aren't present after a re-sync"""
    is_placeholder: bool = False
    """This item has been added to the folder but isn't fully processed yet"""
    backed_data_units_count: int
    storage_location: StorageLocationName
    integration_hash: Optional[UUID]
    url: Optional[str]
    signed_url: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    duration: Optional[float]
    fps: Optional[float]
    height: Optional[int]
    width: Optional[int]
    dicom_instance_uid: Optional[str]
    dicom_study_uid: Optional[str]
    dicom_series_uid: Optional[str]
    frame_count: Optional[int]


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


class FoldersSortBy(CamelStrEnum):
    NAME = auto()
    CREATED_AT = auto()


class ListItemsParams(BaseDTO):
    search: Optional[str]
    is_in_dataset: Optional[bool]
    item_types: List[StorageItemType]
    order: FoldersSortBy
    desc: bool
    page_token: Optional[str]
    page_size: int


class ListFoldersParams(BaseDTO):
    search: Optional[str] = None
    dataset_synced: Optional[bool] = None
    order: FoldersSortBy = FoldersSortBy.NAME
    desc: bool = False
    page_token: Optional[str] = None
    page_size: int = 100
