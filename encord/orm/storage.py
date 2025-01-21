from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import auto
from typing import Dict, List, Optional, Union
from uuid import UUID

from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO, Field
from encord.orm.dataset import DataUnitError, LongPollingStatus

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
    AUDIO = auto()
    NIFTI = auto()
    PLAIN_TEXT = auto()
    PDF = auto()


class StorageUserRole(CamelStrEnum):
    USER = auto()
    ADMIN = auto()


class StorageLocationName(CamelStrEnum):
    ENCORD = auto()
    GCP = auto()
    S3 = auto()
    AZURE = auto()
    OPEN_TELEKOM = auto()  # TODO: Remove when enough people have updated their sdk to include S3_COMPATIBLE below
    DIRECT_ACCESS = auto()
    S3_COMPATIBLE = auto()


class PathElement(BaseDTO):
    uuid: UUID
    parent_uuid: Optional[UUID]
    name: str
    synced_dataset_hash: Optional[UUID]


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
    path_to_root: List[PathElement]


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
    audio_sample_rate: Optional[int]
    audio_bit_depth: Optional[int]
    audio_codec: Optional[str]
    audio_num_channels: Optional[int]


class StorageItemInaccessible(BaseDTO):
    uuid: UUID


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
    """Response of the upload job's long polling request.

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

    units_cancelled_count: int
    """Number of upload job units that have been cancelled."""

    unit_errors: List[DataUnitError]
    """Structured list of per-item upload errors. See :class:`DataUnitError` for more details."""

    file_name: Optional[str] = None
    """Name of the JSON or CSV file that contained the list of URLs to ingest form the cloud bucket. Optional."""


class CustomerProvidedImageMetadata(BaseDTO):
    """Media metadata for an image file; if provided, Encord service will use the values here instead of scanning the files"""

    mime_type: str
    """MIME type of the image file (e.g. `image/jpeg` or `image/png`)."""
    file_size: int
    """Size of the image file in bytes."""
    height: int
    """Height of the image in pixels."""
    width: int
    """Width of the image in pixels."""


class CustomerProvidedVideoMetadata(BaseDTO):
    """Media metadata for a video file; if provided, Encord service will skip frame synchronisation checks
    and will use the values specified here to render the video in the label editor.
    """

    fps: float
    """Frame rate of the video in frames per second."""
    duration: float
    """Video duration in (float) seconds."""
    width: int
    """Width of the video in pixels."""
    height: int
    """Height of the video in pixels."""
    file_size: int
    """Size of the video file in bytes."""
    mime_type: str
    """MIME type of the video file (e.g. `video/mp4` or `video/webm`)."""


class CustomerProvidedAudioMetadata(BaseDTO):
    """Media metadata for an audio file; if provided, Encord service will use the values here instead of scanning the files"""

    duration: float
    """Audio duration in (float) seconds."""
    file_size: int
    """Size of the audio file in bytes."""
    mime_type: str
    """MIME type of the audio file (for example: `audio/mpeg` or `audio/wav`)."""
    sample_rate: int
    """Sample rate (int) in Hz."""
    bit_depth: int
    """Size of each sample (int) in bits."""
    codec: str
    """Codec (for example: mp3, pcm)."""
    num_channels: int
    """Number of channels"""


class CustomerProvidedDicomSeriesDicomFileMetadata(BaseDTO):
    """Metadata for a DICOM file containing required DICOM tags and their values.
    This metadata is used to validate and process DICOM files without needing to access the actual files.

    The `tags` dictionary must contain all required DICOM tags as keys, though their corresponding values may be None.
    Tags should be provided in the format returned by pydicom to_json_dict() method.

    Required tags (using standard DICOM tag numbers):
        - 00080018: SOPInstanceUID
        - 00100020: PatientID
        - 00180050: SliceThickness
        - 00181114: EstimatedRadiographicMagnificationFactor
        - 00181164: ImagerPixelSpacing
        - 0020000D: StudyInstanceUID
        - 0020000E: SeriesInstanceUID
        - 00200013: InstanceNumber
        - 00200032: ImagePositionPatient
        - 00200037: ImageOrientationPatient
        - 00209113: PlanePositionSequence
        - 00209116: PlaneOrientationSequence
        - 00280004: PhotometricInterpretation
        - 00280008: NumberOfFrames
        - 00280010: Rows
        - 00280011: Columns
        - 00280030: PixelSpacing
        - 00281050: WindowCenter
        - 00281051: WindowWidth
        - 00289110: PixelMeasuresSequence
        - 52009229: SharedFunctionalGroupsSequence
        - 52009230: PerFrameFunctionalGroupsSequence

    Missing any of these tags as `tags` dictionary key will raise a validation error.
    """

    tags: Dict[str, Optional[Dict]]


class DataUploadImage(BaseDTO):
    """Data about a single image item to be registered with Encord service."""

    object_url: str
    """"URL of the image file to be registered."""
    title: Optional[str] = None
    """Title of the image item (derived from the URL if omitted)."""
    client_metadata: Dict = Field(default_factory=dict)
    """Custom metadata to be associated with the image item."""
    external_file_type: Literal["IMAGE"] = "IMAGE"
    """Type of the external file."""
    image_metadata: Optional[CustomerProvidedImageMetadata] = None
    """Optional media metadata of the image file (if provided). See :class:`CustomerProvidedImageMetadata` for more details."""

    placeholder_item_uuid: Optional[UUID] = None
    """For system use only."""


class DataUploadVideo(BaseDTO):
    """Data about a video item to be registered with Encord service."""

    object_url: str
    """URL of the video file to be registered."""
    title: Optional[str] = None
    """Title of the video item (derived from the URL if omitted)."""
    client_metadata: Dict = Field(default_factory=dict)
    """Custom metadata to be associated with the video item."""

    external_file_type: Literal["VIDEO"] = "VIDEO"
    """Type of the external file."""
    video_metadata: Optional[CustomerProvidedVideoMetadata] = None
    """Optional media metadata of the video file (if provided). See :class:`CustomerProvidedVideoMetadata` for more details."""

    placeholder_item_uuid: Optional[UUID] = None
    """For system use only."""


class DataUploadNifti(BaseDTO):
    """Data about a NIFTI item to be registered with Encord service."""

    object_url: str
    """URL of the NIFTI file to be registered."""
    title: Optional[str] = None
    """Title of the NIFTI item (derived from the URL if omitted)."""
    client_metadata: Dict = Field(default_factory=dict)
    """Custom metadata to be associated with the NIFTI item."""

    external_file_type: Literal["NIFTI"] = "NIFTI"
    """Type of the external file."""
    placeholder_item_uuid: Optional[UUID] = None
    """For system use only."""


class DataUploadImageGroupImage(BaseDTO):
    """Data about a single image item to be used as a frame in an image group or sequence."""

    url: str
    """URL of the image file to be used as the frame in the image group."""
    title: Optional[str] = None
    """Title of the image item (derived from the URL if omitted)."""
    image_metadata: Optional[CustomerProvidedImageMetadata] = None
    """Optional media metadata of the image file (if provided). See :class:`CustomerProvidedImageMetadata` for more details."""

    placeholder_item_uuid: Optional[UUID] = None
    """For system use only."""


class DataUploadImageGroup(BaseDTO):
    """Data about an image group or image sequence item to be registered with Encord service."""

    images: List[DataUploadImageGroupImage]
    """List of images to be used as frames in the image group. See :class:`DataUploadImageGroupImage` for more details."""
    title: Optional[str]
    """Title of the image group item (requred if using cloud integration)."""
    client_metadata: Dict = Field(default_factory=dict)
    """Custom metadata to be associated with the image group item."""
    create_video: bool = False
    """If set to `True`, create an image sequence backed by a video file uploaded to the cloud storage."""

    external_file_type: Literal["IMG_GROUP"] = "IMG_GROUP"
    """Type of the external file."""
    cluster_by_resolution: bool = False
    """For system use only."""


class DataUploadImageGroupFromItems(BaseDTO):
    """Data about an image group item to be created from previously uploaded images."""

    image_items: List[UUID]
    """List of image items to be used as frames in the image group."""
    title: Optional[str]
    """Title of the image group item (required if using cloud integration)."""
    client_metadata: Dict = Field(default_factory=dict)
    """Custom metadata to be associated with the image group."""
    create_video: bool
    """If set to `True`, create an image sequence backed by a video file uploaded to the cloud storage."""
    video_url_prefix: Optional[str] = None
    """URL prefix for the video file to be created from the image group."""

    external_file_type: Literal["IMG_GROUP_FROM_ITEMS"] = "IMG_GROUP_FROM_ITEMS"
    """Type of the external file."""
    cluster_by_resolution: bool = False
    """For system use only."""


class DataUploadDicomSeriesDicomFile(BaseDTO):
    """Data about a single DICOM file to be used in a series item."""

    url: str
    """URL of the DICOM file to be registered with Encord service."""
    title: Optional[str]
    """Title of the DICOM file (derived from the URL if omitted)."""
    dicom_metadata: Optional[CustomerProvidedDicomSeriesDicomFileMetadata] = None
    """Optional media metadata of the DICOM file (if provided). See :class:`CustomerProvidedDicomSeriesDicomFileMetadata` for more details."""

    placeholder_item_uuid: Optional[UUID] = None
    """For system use only."""


class DataUploadDicomSeries(BaseDTO):
    """Data about a DICOM series item to be registered with Encord service."""

    dicom_files: List[DataUploadDicomSeriesDicomFile]
    """List of DICOM files to be used in the series item. See :class:`DataUploadDicomSeriesDicomFile` for more details."""
    title: Optional[str]
    """Title of the DICOM series item (required if using cloud integration)."""
    client_metadata: Dict = Field(default_factory=dict)
    """Custom metadata to be associated with the DICOM series item."""

    external_file_type: Literal["DICOM"] = "DICOM"
    """Type of the external file."""


class DataUploadText(BaseDTO):
    object_url: str
    """URL of the text (TXT, HTML, etc) file to be registered with Encord service."""
    title: Optional[str] = None
    """Title of the file (derived from the URL if omitted)."""
    client_metadata: dict = Field(default_factory=dict)
    """Custom metadata to be associated with the file."""

    external_file_type: Literal["PLAIN_TEXT"] = "PLAIN_TEXT"
    """Type of the external file."""

    placeholder_item_uuid: Optional[UUID] = None
    """For system use only."""


class DataUploadPDF(BaseDTO):
    object_url: str
    """URL of the PDF file to be registered with Encord service."""
    title: Optional[str] = None
    """Title of the file (derived from the URL if omitted)."""
    client_metadata: dict = Field(default_factory=dict)
    """Custom metadata to be associated with the file."""

    external_file_type: Literal["PDF"] = "PDF"
    """Type of the external file."""

    placeholder_item_uuid: Optional[UUID] = None
    """For system use only."""


class DataUploadAudio(BaseDTO):
    """Data about an audio item to be registered with Encord service."""

    object_url: str
    """URL of the audio file to be registered."""
    title: Optional[str] = None
    """Title of the audio item (derived from the URL if omitted)."""
    client_metadata: Dict = Field(default_factory=dict)
    """Custom metadata to be associated with the audio item."""

    audio_metadata: Optional[CustomerProvidedAudioMetadata] = None
    """Optional media metadata of the audio file (if provided). See :class:`CustomerProvidedAudioMetadata` for more details."""
    external_file_type: Literal["AUDIO"] = "AUDIO"
    """Type of the external file."""

    placeholder_item_uuid: Optional[UUID] = None
    """For system use only."""


class DataUploadItems(BaseDTO):
    """A collection of items to be registered with Encord service.

    A more structured alternative to using a JSON file.
    """

    videos: List[DataUploadVideo] = Field(default_factory=list)
    """List of video items to be registered. See :class:`DataUploadVideo` for more details."""

    image_groups: List[DataUploadImageGroup] = Field(default_factory=list)
    """List of image group items to be registered. See :class:`DataUploadImageGroup` for more details."""

    dicom_series: List[DataUploadDicomSeries] = Field(default_factory=list)
    """List of DICOM series items to be registered. See :class:`DataUploadDicomSeries` for more details."""

    images: List[DataUploadImage] = Field(default_factory=list)
    """List of image items to be registered. See :class:`DataUploadImage` for more details."""

    image_groups_from_items: List[DataUploadImageGroupFromItems] = Field(default_factory=list)
    """List of image group items to be created from previously uploaded images.
    See :class:`DataUploadImageGroupFromItems` for more details."""

    audio: List[DataUploadAudio] = Field(default_factory=list)
    """List of audio items to be registered. See :class:`DataUploadAudio` for more details."""

    nifti: List[DataUploadNifti] = Field(default_factory=list)
    """List of NIFTI items to be registered. See :class:`DataUploadNifti` for more details."""

    text: List[DataUploadText] = Field(default_factory=list)
    """List of text items to be registered. See :class:`DataUploadText` for more details."""

    pdf: List[DataUploadPDF] = Field(default_factory=list)
    """List of PDF items to be registered. See :class:`DataUploadPDF` for more details."""

    skip_duplicate_urls: bool = False
    """If set to `True`, Encord service will skip items with URLs that already exist in the same folder.
    Otherwise, duplicate items will be created."""

    upsert_metadata: bool = False
    """If set to `True`, Encord service will update metadata of existing items with the same URL in the same folder.
    This flag has no effect if `skip_duplicate_urls` is set to `False`."""


class DatasetDataLongPollingParams(BaseDTO):
    data_items: Optional[DataUploadItems]
    files: Optional[dict]
    integration_id: Optional[UUID]
    ignore_errors: bool
    folder_uuid: Optional[UUID]
    file_name: Optional[str]


class PostUploadJobParams(BaseDTO):
    data_items: Optional[DataUploadItems] = None
    external_files: Optional[dict] = None
    integration_hash: Optional[UUID] = None
    ignore_errors: bool = False
    file_name: Optional[str] = None


class GetUploadJobParams(BaseDTO):
    timeout_seconds: int = 60


class FoldersSortBy(CamelStrEnum):
    NAME = auto()
    CREATED_AT = auto()


class ListItemsParams(BaseDTO):
    search: Optional[str]
    is_recursive: Optional[bool] = False
    is_in_dataset: Optional[bool]
    item_types: List[StorageItemType]
    include_org_access: Optional[bool] = None
    order: FoldersSortBy
    desc: bool
    page_token: Optional[str]
    page_size: int
    sign_urls: bool


class ListFoldersParams(BaseDTO):
    search: Optional[str] = None
    is_recursive: Optional[bool] = False
    dataset_synced: Optional[bool] = None
    include_org_access: Optional[bool] = None
    order: FoldersSortBy = FoldersSortBy.NAME
    desc: bool = False
    page_token: Optional[str] = None
    page_size: int = 100


class PatchItemPayload(BaseDTO):
    name: Optional[str] = None
    description: Optional[str] = None
    client_metadata: Optional[dict] = None


class PatchFolderPayload(BaseDTO):
    name: Optional[str] = None
    description: Optional[str] = None
    client_metadata: Optional[dict] = None


class PatchFoldersBulkPayload(BaseDTO):
    folder_patches: Dict[str, PatchFolderPayload]


class StorageFolderSummary(BaseDTO):
    files: int
    folders: int
    videos: int
    images: int
    image_groups: int
    image_sequences: int
    dicom_files: int
    dicom_series: int
    niftis: int
    audios: int
    pdfs: int
    plain_texts: int
    tombstones: int
    upload_jobs: int
    total_size: float


class ItemShortInfo(BaseDTO):
    uuid: UUID
    name: str
    parent_uuid: UUID
    parent_name: str
    item_type: StorageItemType


class DatasetShortInfo(BaseDTO):
    dataset_hash: str
    backing_folder_uuid: Optional[UUID]
    title: str
    data_hashes: List[UUID]
    data_units_created_at: datetime


class StorageItemSummary(BaseDTO):
    """A summary of item usage in the system"""

    frame_in_groups: int
    """A number of group items (DICOM_SERIES, IMAGE_GROUP, IMAGE_SEQUENCE) that contain this item"""
    accessible_group_items: List[ItemShortInfo]
    """List of group items that contain this item (only those that the user has access to,
    so the length of this list can be less than `frame_in_groups`)"""
    used_in_datasets: int
    """A number of datasets that contain this item as a `DataRow`"""
    accessible_datasets: List[DatasetShortInfo]
    """List of datasets that contain this item as a `DataRow` (only those that the user has access to, so
    the length of this list can be less than `used_in_datasets`)"""


class DeleteItemsParams(BaseDTO):
    remove_unused_frames: bool


class DeleteItemsPayload(BaseDTO):
    child_uuids: List[UUID]
    remove_unused_frames: bool


class DeleteItemsResponse(BaseDTO):
    removed_items_count: int
    removed_folders_count: int


class MoveItemsPayload(BaseDTO):
    item_uuids: List[UUID]
    new_parent_uuid: UUID
    allow_synced_dataset_move: bool = False


class MoveFoldersPayload(BaseDTO):
    folder_uuids: List[UUID]
    new_parent_uuid: Optional[UUID]


class GetItemParams(BaseDTO):
    sign_url: bool


class GetChildItemsParams(BaseDTO):
    sign_urls: bool = False


class GetItemsBulkPayload(BaseDTO):
    item_uuids: List[UUID]
    sign_urls: bool = False


class PatchItemsBulkPayload(BaseDTO):
    item_patches: Dict[str, PatchItemPayload]


@dataclass
class BundledPatchItemPayload:
    item_patches: Dict[str, PatchItemPayload]

    def add(self, other: BundledPatchItemPayload) -> BundledPatchItemPayload:
        self.item_patches.update(other.item_patches)
        return self


@dataclass
class BundledPatchFolderPayload:
    folder_patches: Dict[str, PatchFolderPayload]

    def add(self, other: BundledPatchFolderPayload) -> BundledPatchFolderPayload:
        self.folder_patches.update(other.folder_patches)
        return self


class ReencodeVideoItemsRequest(BaseDTO):
    storage_items: List[UUID]
    process_title: str
    force_full_reencoding: bool


class JobStatus(CamelStrEnum):
    SUBMITTED = auto()
    DONE = auto()
    ERROR = auto()


class ReencodeVideoItemsResponse(BaseDTO):
    status: JobStatus
    result: Optional[Union[list, dict]]


class StorageItemsMigratePayload(BaseDTO):
    urls_map: Optional[Dict[str, Optional[str]]]
    items_map: Optional[Dict[UUID, Optional[str]]]
    from_integration_hash: Optional[UUID] = None
    to_integration_hash: Optional[UUID] = None
    validate_access: bool = False
    skip_missing: bool = False


class AddDataToFolderJobCancelResponse(BaseDTO):
    units_cancelled_count: int
