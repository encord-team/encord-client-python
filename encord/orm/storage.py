from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import auto
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from encord.common.deprecated import deprecated
from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO, Field, RootModelDTO
from encord.orm.dataset import DataUnitError, LongPollingStatus
from encord.orm.group_layout import DataGroupLayout, DataGroupShortInfo, LayoutSettings

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore[assignment]


class StorageItemType(CamelStrEnum):
    """Type of item stored in Encord storage.

    **Values:**

    - **VIDEO:** A video file.
    - **IMAGE:** A single image.
    - **GROUP:** A generic grouped item.
    - **IMAGE_GROUP:** A group of images treated as a single item.
    - **IMAGE_SEQUENCE:** An image sequence backed by a video or ordered frames.
    - **DICOM_FILE:** A single DICOM file.
    - **DICOM_SERIES:** A DICOM series composed of multiple DICOM files.
    - **AUDIO:** An audio file.
    - NIFTI:** A NIFTI volume.
    - **PLAIN_TEXT:** A text file (for example TXT, HTML, JSON).
    - **PDF:** A PDF document.
    - **SCENE:** A scene. For example, a single point cloud data file or a composition of multiple assets like videos and point cloud data files.
    """

    VIDEO = auto()
    IMAGE = auto()
    GROUP = auto()
    IMAGE_GROUP = auto()
    IMAGE_SEQUENCE = auto()
    DICOM_FILE = auto()
    DICOM_SERIES = auto()
    AUDIO = auto()
    NIFTI = auto()
    PLAIN_TEXT = auto()
    PDF = auto()
    SCENE = auto()


class StorageUserRole(CamelStrEnum):
    """Role of a user in the context of a storage folder or item.

    **Values:**

    - **USER:** Standard user with access to the item.
    - **ADMIN:** User with administrative privileges on the item.
    """

    USER = auto()
    ADMIN = auto()


class StorageLocationName(CamelStrEnum):
    """Storage backends supported by Encord.

    **Values:**

    - **ENCORD:** Encord-managed storage.
    - **GCP:** Google Cloud Storage.
    - **S3:** Amazon S3.
    - **AZURE:** Azure Blob Storage.
    - **OPEN_TELEKOM:** Open Telekom Cloud (legacy alias, superseded by S3_COMPATIBLE).
    - **DIRECT_ACCESS:** Direct-access storage.
    - **S3_COMPATIBLE:** Generic S3-compatible storage backend.
    """

    ENCORD = auto()
    GCP = auto()
    S3 = auto()
    AZURE = auto()
    OPEN_TELEKOM = auto()  # TODO: Remove when enough people have updated their sdk to include S3_COMPATIBLE below
    DIRECT_ACCESS = auto()
    S3_COMPATIBLE = auto()


class PathElement(BaseDTO):
    """Single step in the path from a storage folder to the root.

    Args:
        uuid: UUID of this path element (folder).
        parent_uuid: UUID of the parent path element, if any.
        name: Name of the folder.
        synced_dataset_hash: UUID of the dataset that is synced with this folder, if any.
    """

    uuid: UUID
    parent_uuid: Optional[UUID]
    name: str
    synced_dataset_hash: Optional[UUID]


class StorageFolder(BaseDTO):
    """Folder in Encord storage.

    Args:
        uuid:  UUID of the folder.
        parent: UUID of the parent folder, if any.
        name: Name of the folder.
        description: Optional description of the folder.
        client_metadata: Optional custom metadata associated with the folder.
        owner: Email or identifier of the folder owner.
        created_at: Timestamp when the folder was created.
        last_edited_at: Timestamp when the folder was last modified.
        user_role: Role of the current user in this folder.
        synced_dataset_hash: UUID of the dataset synced with this folder, if any.
        path_to_root: Path from this folder to the root, represented as a list
            of :class:`PathElement` instances.
    """

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
    """Item in Encord storage (file, group, DICOM series, etc.).

    Args:
        uuid: UUID of the storage item.
        parent:  UUID of the parent folder containing this item.
        item_type: Type of the storage item (video, image, group, etc.).
        name: Name of the item.
        description: Optional description of the item.
        client_metadata: Optional custom metadata associated with the item.
        owner: Email or identifier of the item owner.
        created_at: Timestamp when the item was created.
        last_edited_at: Timestamp when the item was last modified.
        is_tombstone: This item has been deleted but the link is retained for consistency reasons.
        Mostly for items in the 'cloud linked folders' that are referenced but aren't present after a re-sync.
        is_placeholder: This item has been added to the folder but isn't fully processed yet.
        backed_data_units_count:  Number of data units backed by this storage item.
        storage_location: Storage backend where the item resides.
        integration_hash: UUID of the integration used for this item, if any.
        url: Raw URL of the storage object, if available.
        signed_url:  Signed URL for temporary access to the storage object.
        file_size:  Size of the file in bytes, if known.
        mime_type: MIME type of the file, if known.
        duration:  Duration in seconds (for temporal media), if known.
        fps:  Frame rate value (for video), if known.
        height: Height in pixels (for image/video), if known.
        width: Width in pixels (for image/video), if known.
        dicom_instance_uid:  DICOM instance UID, if applicable.
        dicom_study_uid: DICOM study UID, if applicable.
        dicom_series_uid: DICOM series UID, if applicable.
        frame_count: Number of frames for multi-frame media, if known.
        audio_sample_rate: Sample rate of the audio track in Hz, if known.
        audio_bit_depth: Bit depth of the audio track, if known.
        audio_codec: Codec name of the audio track, if known.
        audio_num_channels: Number of audio channels, if known.
    """

    uuid: UUID
    parent: UUID
    item_type: StorageItemType
    name: str
    description: str = ""
    client_metadata: str
    owner: str
    created_at: datetime
    last_edited_at: datetime
    is_tombstone: bool = False
    is_placeholder: bool = False
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
    """Stub object used when a storage item is inaccessible.

    Args:
        uuid:
            UUID of the item that cannot be accessed.
    """

    uuid: UUID


class CloudSyncedFolderParams(BaseDTO):
    """
    Parameters for creating a cloud-synced folder in Encord storage.

    A cloud-synced folder maintains synchronization link between an Encord
    storage folder and an external cloud storage location (bucket/folder). This allows you to
    manage files in your preferred cloud provider while making them available for use in Encord.
    """

    integration_uuid: UUID
    """
    UUID of the cloud storage integration to use.

    This UUID refers to a preconfigured integration in Encord that contains
    authentication credentials and settings for a cloud storage provider.
    The integration must be set up in the Encord platform before creating
    a cloud-synced folder.
    """

    remote_url: str
    """
    URL or path to the cloud storage location to sync with.

    The format depends on the cloud storage provider:
    - Amazon S3: "s3://bucket-name/path/"
    - Google Cloud Storage: "gs://bucket-name/path/"
    - Azure Blob Storage: "https://account.blob.core.windows.net/container/path/"
    - S3-compatible services: "https://endpoint/bucket-name/path/"

    The folder will be synced recursively, and all supported file types
    will be imported into Encord.
    """


class CreateStorageFolderPayload(BaseDTO):
    """Payload for creating a storage folder.

    Args:
        name: Name of the new folder.
        description: Optional description of the folder.
        parent:  UUID of the parent folder under which to create this folder.
        client_metadata: Optional custom metadata associated with the folder.
        cloud_synced_folder_params: Optional configuration for creating a cloud-synced folder
            that is linked to an external storage location.
    """

    name: str
    description: Optional[str]
    parent: Optional[UUID]
    client_metadata: Optional[str]
    cloud_synced_folder_params: Optional[CloudSyncedFolderParams] = None


class DataGroupGrid(BaseDTO):
    """Grid-based layout for a data group.

    Args:
        layout_contents: Ordered list of item UUIDs to display in the grid.
        name: Optional name of the data group.
        client_metadata: Optional custom metadata to associate with the data group.
    """

    layout_type: Literal["default-grid"] = "default-grid"
    layout_contents: List[UUID]
    name: Optional[str] = None
    client_metadata: Optional[Dict[str, Any]] = None


class DataGroupCarousel(BaseDTO):
    """Carousel layout for a data group.

    Args:
        layout_contents: Ordered list of item UUIDs to display in the carousel.
        name: Optional name of the data group.
        client_metadata: Optional custom metadata to associate with the data group.
    """

    layout_type: Literal["default-list"] = "default-list"
    layout_contents: List[UUID]
    name: Optional[str] = None
    client_metadata: Optional[Dict[str, Any]] = None


@deprecated(version=None, alternative="DataGroupCarousel")
class DataGroupList(DataGroupCarousel):
    """
    Deprecated, will be removed in a future release. Use `DataGroupCarousel` instead.
    """


class DataGroupCustom(BaseDTO):
    """Custom layout for a data group.

    Args:
        name: Optional name of the data group.
        layout_contents: Mapping from arbitrary keys to item UUIDs.
        layout: Arbitrary layout configuration structure.
        settings: Optional extra settings for the layout.
        client_metadata: Optional custom metadata to associate with the data group.
    """

    layout_type: Literal["custom"] = "custom"
    name: Optional[str] = None
    layout_contents: Dict[str, UUID]
    layout: Union[Dict, DataGroupLayout]
    settings: Optional[Union[Dict, LayoutSettings]] = None
    client_metadata: Optional[Dict[str, Any]] = None


DataGroupInput = Union[DataGroupGrid, DataGroupCarousel, DataGroupCustom]


class CreateDataGroupsResponse(RootModelDTO[List[UUID]]):
    """Response returned after creating multiple data groups.

    The root value is a list of UUIDs of the created data group storage items.
    """


class UploadSignedUrlsPayload(BaseDTO):
    """Request payload for generating signed URLs for uploads.

    Args:
        item_type: Type of storage item that will be uploaded.
        count: Number of signed URLs to generate.
        frames_subfolder_name: Optional subfolder name to use for frame-based uploads.
    """

    item_type: StorageItemType
    count: int
    frames_subfolder_name: Optional[str]


class UploadSignedUrl(BaseDTO):
    """Single signed URL returned for an upload.

    Args:
        item_uuid: UUID of the placeholder storage item to be filled.
        object_key: Object key or path in the underlying storage backend.
        signed_url: Signed URL that can be used to upload the content.
    """

    item_uuid: UUID
    object_key: str
    signed_url: str


class StorageItemWithName(BaseDTO):
    """Storage item reference with a resolved name.

    Args:
        item_uuid: UUID of the storage item.
        name: Display name of the item.
    """

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
    """Number of upload job units that have been canceled."""

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
    """Media metadata for a video file; if provided, Encord service will skip frame synchronization checks
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
    """Media metadata for an audio file. The Encord platform uses the specified values instead of scanning the files."""

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


class CustomerProvidedTextMetadata(BaseDTO):
    """Media metadata for a text file. The Encord platform uses the specified values instead of scanning the files."""

    file_size: int
    """Size of the text file in bytes."""
    mime_type: str
    """MIME type of the text file (for example: `application/json` or `text/plain…`)."""


class CustomerProvidedPdfMetadata(BaseDTO):
    """Media metadata for a PDF file. The Encord platform uses the specified values instead of scanning the files."""

    file_size: int
    """Size of the PDF file in bytes."""
    num_pages: int
    """Number of pages in the PDF file."""


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
    """Title of the image group item (required if using cloud integration)."""
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
    """Data about a text file to be registered with Encord service.

    Args:
        object_url: URL of the text (TXT, HTML, etc.) file to be registered.
        title: Title of the file (derived from the URL if omitted).
        client_metadata: Custom metadata to be associated with the file.
        external_file_type: Type of the external file, always ``"PLAIN_TEXT"``.
        text_metadata: Optional media metadata of the text file. See :class:`CustomerProvidedTextMetadata` for more details.
        placeholder_item_uuid: For system use only.
    """

    object_url: str
    title: Optional[str] = None
    client_metadata: dict = Field(default_factory=dict)
    external_file_type: Literal["PLAIN_TEXT"] = "PLAIN_TEXT"
    text_metadata: Optional[CustomerProvidedTextMetadata] = None
    placeholder_item_uuid: Optional[UUID] = None


class DataUploadPDF(BaseDTO):
    """Data about a PDF file to be registered with Encord service.

    Args:
        object_url: URL of the PDF file to be registered.
        title: Title of the PDF file (derived from the URL if omitted).
        client_metadata: Custom metadata to be associated with the file.
        pdf_metadata: Optional media metadata of the PDF file. See :class:`CustomerProvidedPdfMetadata` for more information.
        external_file_type: Type of the external file, always ``"PDF"``.
        placeholder_item_uuid: For system use only.
    """

    object_url: str
    title: Optional[str] = None
    client_metadata: dict = Field(default_factory=dict)
    pdf_metadata: Optional[CustomerProvidedPdfMetadata] = None
    external_file_type: Literal["PDF"] = "PDF"
    placeholder_item_uuid: Optional[UUID] = None


class DataUploadAudio(BaseDTO):
    """Data about an audio item to be registered with Encord service.

    Args:
        object_url: URL of the audio file to be registered.
        title: Title of the audio item (derived from the URL if omitted).
        client_metadata: Custom metadata to be associated with the audio item.
        audio_metadata: Optional media metadata of the audio file (if provided). See :class:`CustomerProvidedAudioMetadata` for more details.
        external_file_type: Type of the external file, always ``"AUDIO"``.
        placeholder_item_uuid: For system use only.
    """

    object_url: str
    title: Optional[str] = None
    client_metadata: Dict = Field(default_factory=dict)
    audio_metadata: Optional[CustomerProvidedAudioMetadata] = None
    external_file_type: Literal["AUDIO"] = "AUDIO"
    placeholder_item_uuid: Optional[UUID] = None


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
    """Parameters for long-polling dataset data upload or import.

    Args:
        data_items: Structured items to be uploaded as part of the job.
        files: Optional mapping of filenames to file contents (for file-based
            imports such as JSON manifests).
        integration_id: UUID of the integration used to access external storage.
        ignore_errors: If ``True``, continue processing other items even if some
            fail.
        folder_uuid: UUID of the storage folder where data should be registered.
        file_name: Optional name of the manifest file associated with the job.
    """

    data_items: Optional[DataUploadItems]
    files: Optional[dict]
    integration_id: Optional[UUID]
    ignore_errors: bool
    folder_uuid: Optional[UUID]
    file_name: Optional[str]


class PostUploadJobParams(BaseDTO):
    """Parameters for starting an upload job.

    Args:
        data_items: Structured items to be uploaded as part of the job.
        external_files: Mapping of filenames to file contents for file-based imports.
        integration_hash: UUID of the integration used to access external storage.
        ignore_errors: If ``True``, continue processing other items even if some
            fail.
        file_name: Optional name of the manifest file associated with the job.
    """

    data_items: Optional[DataUploadItems] = None
    external_files: Optional[dict] = None
    integration_hash: Optional[UUID] = None
    ignore_errors: bool = False
    file_name: Optional[str] = None


class GetUploadJobParams(BaseDTO):
    """Parameters for polling the status of an upload job.

    Args:
        timeout_seconds: Maximum number of seconds to wait before returning the
            current job status.
    """

    timeout_seconds: int = 60


class FoldersSortBy(CamelStrEnum):
    """Sorting options for listing items or folders.

    **Values:**

     - **NAME:** Sort by name.
     - **CREATED_AT:** Sort by creation time.
    """

    NAME = auto()
    CREATED_AT = auto()


class ListItemsParams(BaseDTO):
    """Parameters for listing storage items in a folder.

    Args:
        search: Optional free-text search string to filter items.
        is_recursive: If ``True``, include items in nested subfolders.
        is_in_dataset: If set, filter items that are (or are not) linked to datasets.
        item_types: List of item types to include in the response.
        include_org_access: If ``True``, include items accessible via organisation-level
            access.
        order: Sort order for the results.
        desc: If ``True``, sort in descending order.
        page_token: Token for fetching the next page of results.
        page_size: Maximum number of items to return.
        sign_urls: If ``True``, include signed URLs for the items in the
            response.
    """

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
    """Parameters for listing folders in Encord storage.

    Args:
        search: Optional free-text search string to filter folders.
        is_recursive: If ``True``, include nested subfolders in the listing.
        dataset_synced: If set, filter folders that are (or are not) synced with a
            dataset.
        include_org_access: If ``True``, include folders accessible via organisation-level
            access.
        order: Field to sort folders by.
        desc: If ``True``, sort in descending order.
        page_token: Token for fetching the next page of results.
        page_size: Maximum number of folders to return (defaults to 100).
    """

    search: Optional[str] = None
    is_recursive: Optional[bool] = False
    dataset_synced: Optional[bool] = None
    include_org_access: Optional[bool] = None
    order: FoldersSortBy = FoldersSortBy.NAME
    desc: bool = False
    page_token: Optional[str] = None
    page_size: int = 100


class PatchItemPayload(BaseDTO):
    """Payload for partially updating a storage item.

    Args:
        name: New name for the item, if updating.
        description: New description for the item, if updating.
        client_metadata: New custom metadata to merge or overwrite, depending on API semantics.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    client_metadata: Optional[dict] = None


class PatchFolderPayload(BaseDTO):
    """Payload for partially updating a storage folder.

    Args:
        name: New name for the folder, if updating.
        description: New description for the folder, if updating.
        client_metadata: New custom metadata to merge or overwrite, depending on API semantics.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    client_metadata: Optional[dict] = None


class PatchFoldersBulkPayload(BaseDTO):
    """Payload for applying partial updates to multiple folders.

    Args:
        folder_patches: Mapping from folder UUID (as string) to patch payload to
            apply to that folder.
    """

    folder_patches: Dict[str, PatchFolderPayload]


class StorageFolderSummary(BaseDTO):
    """Summary statistics for a storage folder.

    Args:
        files: Total number of files in the folder.
        folders: Total number of subfolders.
        videos: Number of video items.
        images: Number of image items.
        image_groups: Number of image group items.
        image_sequences: Number of image sequence items.
        dicom_files: Number of DICOM file items.
        dicom_series: Number of DICOM series items.
        niftis: Number of NIFTI items.
        audios: Number of audio items.
        pdfs: Number of PDF items.
        plain_texts: Number of plain text items.
        tombstones: Number of tombstone items.
        upload_jobs: Number of upload jobs associated with this folder.
        total_size: Approximate total size of all items in bytes.
    """

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
    """Short information about a storage item, typically used in summaries.

    Args:
        uuid: UUID of the item.
        name: Name of the item.
        parent_uuid: UUID of the parent folder.
        parent_name: Name of the parent folder.
        item_type: Type of the item.
    """

    uuid: UUID
    name: str
    parent_uuid: UUID
    parent_name: str
    item_type: StorageItemType


class DatasetShortInfo(BaseDTO):
    """Short information about a dataset that uses a storage item.

    Args:
        dataset_hash: Identifier of the dataset.
        backing_folder_uuid: UUID of the backing folder for the dataset, if any.
        title: Title of the dataset.
        data_hashes: List of data unit identifiers linked to the dataset.
        data_units_created_at: Timestamp when the data units were created.
    """

    dataset_hash: str
    backing_folder_uuid: Optional[UUID]
    title: str
    data_hashes: List[UUID]
    data_units_created_at: datetime


class _StorageItemPrivateSummary(BaseDTO):
    frame_in_groups: int
    accessible_group_items: List[ItemShortInfo]
    used_in_datasets: int
    accessible_datasets: List[DatasetShortInfo]
    group_layout: Optional[DataGroupShortInfo] = None


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
    data_group: Optional[DataGroupShortInfo] = None
    """Data group layout information. Only populated when the item is a GROUP."""


def _to_storage_item_summary(private_summary: _StorageItemPrivateSummary) -> StorageItemSummary:
    return StorageItemSummary(
        frame_in_groups=private_summary.frame_in_groups,
        accessible_group_items=private_summary.accessible_group_items,
        used_in_datasets=private_summary.used_in_datasets,
        accessible_datasets=private_summary.accessible_datasets,
        data_group=private_summary.group_layout,
    )


class DeleteItemsParams(BaseDTO):
    """Parameters controlling how storage items are deleted.

    Args:
        remove_unused_frames: If ``True``, also remove frames that are no longer used by
            any group items after deletion.
    """

    remove_unused_frames: bool


class DeleteItemsPayload(BaseDTO):
    """Payload for deleting storage items.

    Args:
        child_uuids: UUIDs of the child items to delete.
        remove_unused_frames: If ``True``, also remove frames that are no longer referenced
            after deletion.
    """

    child_uuids: List[UUID]
    remove_unused_frames: bool


class DeleteItemsResponse(BaseDTO):
    """Response returned after deleting storage items.

    Args:
        removed_items_count: Number of storage items removed.
        removed_folders_count: Number of folders removed.
    """

    removed_items_count: int
    removed_folders_count: int


class MoveItemsPayload(BaseDTO):
    """Payload for moving storage items to a new folder.

    Args:
        item_uuids: UUIDs of the items to move.
        new_parent_uuid: UUID of the destination folder.
        allow_synced_dataset_move: If ``True``, allow moving items that are linked to synced
            datasets.
    """

    item_uuids: List[UUID]
    new_parent_uuid: UUID
    allow_synced_dataset_move: bool = False


class MoveFoldersPayload(BaseDTO):
    """Payload for moving folders to a new parent folder.

    Args:
        folder_uuids: UUIDs of the folders to move.
        new_parent_uuid: UUID of the destination folder, or ``None`` to move to root.
    """

    folder_uuids: List[UUID]
    new_parent_uuid: Optional[UUID]


class GetItemParams(BaseDTO):
    """Parameters for fetching detailed information about a storage item.

    Args:
        sign_url: If ``True``, include a signed URL for temporary access to the
            item in the response.
    """

    sign_url: bool


class _GetItemSummaryParams(BaseDTO):
    """Parameters for fetching item summary information.

    Args:
        include_group_layout: If ``True``, include the data group layout in the response.
            Only applicable for GROUP item types.
    """

    include_group_layout: bool = False


class GetChildItemsParams(BaseDTO):
    """Parameters for listing direct children of a storage folder.

    Args:
        sign_urls: If ``True``, include signed URLs for the items in the
            response.
    """

    sign_urls: bool = False


class GetItemsBulkPayload(BaseDTO):
    """Payload for fetching multiple storage items at once.

    Args:
        item_uuids: UUIDs of the items to fetch.
        sign_urls: If ``True``, include signed URLs for the items in the
            response.
    """

    item_uuids: List[UUID]
    sign_urls: bool = False


class PatchItemsBulkPayload(BaseDTO):
    """Payload for applying partial updates to multiple storage items.

    Args:
        item_patches: Mapping from item UUID (as string) to patch payload to apply
            to that item.
    """

    item_patches: Dict[str, PatchItemPayload]


@dataclass
class BundledPatchItemPayload:
    """Accumulator for batched item patch operations.

    Args:
        item_patches: Mapping from item UUID (as string) to patch payload to apply
            to that item.
    """

    item_patches: Dict[str, PatchItemPayload]

    def add(self, other: BundledPatchItemPayload) -> BundledPatchItemPayload:
        self.item_patches.update(other.item_patches)
        return self


@dataclass
class BundledPatchFolderPayload:
    """Accumulator for batched folder patch operations.

    Args:
        folder_patches: Mapping from folder UUID (as string) to patch payload to
            apply to that folder.
    """

    folder_patches: Dict[str, PatchFolderPayload]

    def add(self, other: BundledPatchFolderPayload) -> BundledPatchFolderPayload:
        self.folder_patches.update(other.folder_patches)
        return self


class ReencodeVideoItemsRequest(BaseDTO):
    """Request to re-encode a set of video storage items.

    Args:
        storage_items: UUIDs of the storage items (videos) to re-encode.
        process_title: Human-readable title for the re-encode job.
        force_full_reencoding: If ``True``, force re-encoding even if a compatible version
            already exists.
    """

    storage_items: List[UUID]
    process_title: str
    force_full_reencoding: bool


class JobStatus(CamelStrEnum):
    """Status of a background job.

    **Values**:

    - **SUBMITTED:** Job has been submitted and is waiting to start.
    - **DONE:** Job has completed successfully.
    - **ERROR:** Job has failed.
    """

    SUBMITTED = auto()
    DONE = auto()
    ERROR = auto()


class ReencodeVideoItemsResponse(BaseDTO):
    """Response returned after starting or querying a re-encode job.

    Args:
        status: Current status of the re-encode job.
        result: Optional result payload, for example a list or dict
            with additional information about the re-encoded items.
    """

    status: JobStatus
    result: Optional[Union[list, dict]]


class StorageItemsMigratePayload(BaseDTO):
    """Payload for migrating storage items between integrations.

    Args:
        urls_map: Optional mapping from source URLs to target URLs. If the value
            is ``None``, the item for that URL will be skipped.
        items_map: Optional mapping from item UUIDs to new URLs. If the value
            is ``None``, the item will be skipped.
        from_integration_hash: UUID of the source integration to migrate from.
        to_integration_hash: UUID of the target integration to migrate to.
        validate_access: If ``True``, validate that the SDK has access to the target
            integration before migrating.
        skip_missing: If ``True``, skip items that cannot be found instead of
            failing the entire migration.
    """

    urls_map: Optional[Dict[str, Optional[str]]]
    items_map: Optional[Dict[UUID, Optional[str]]]
    from_integration_hash: Optional[UUID] = None
    to_integration_hash: Optional[UUID] = None
    validate_access: bool = False
    skip_missing: bool = False


class AddDataToFolderJobCancelResponse(BaseDTO):
    """Response returned after canceling an add-data-to-folder job.

    Arg:
        units_cancelled_count: Number of individual job units that were canceled.
    """

    units_cancelled_count: int


class SyncPrivateDataWithCloudSyncedFolderGetResultParams(BaseDTO):
    """Parameters for polling the status of a cloud-synced folder sync job.

    Args:
        timeout_seconds: Maximum number of seconds to wait before returning the
            current synchronization status.
    """

    timeout_seconds: int


class SyncPrivateDataWithCloudSyncedFolderStatus(CamelStrEnum):
    """
    Enumeration representing the possible states of a cloud-synced folder synchronization job.

    This enum is used to track the life cycle of a synchronization operation between
    an Encord storage folder and its linked cloud storage bucket.
    """

    PENDING = auto()
    """
    The synchronization job is currently in progress.

    This status indicates that either:
    - The job is queued and waiting to be processed
    - The job is actively processing bucket content
    - The job is creating or updating items in the Encord storage folder
    """

    DONE = auto()
    """
    The synchronization job has successfully completed.

    This status indicates that all phases of the synchronization (bucket scanning,
    item creation/updating/tombstoning) have been completed without critical errors.
    Note that individual items may still have failed to process (check upload_jobs_units_error).
    """

    ERROR = auto()
    """
    The synchronization job encountered a critical error.

    This status indicates that a severe error occurred during synchronization,
    such as:
    - Unable to access the cloud storage bucket
    - Database transaction failures
    - Other system-level errors

    When in ERROR state, the sync operation is considered failed and should be restarted.
    """

    CANCELLED = auto()
    """
    The synchronization job was manually canceled.

    This status indicates that the job was explicitly terminated before completion.
    """


class SyncPrivateDataWithCloudSyncedFolderGetResultResponse(BaseDTO):
    """
    Response object representing the status and results of a cloud-synced folder synchronization job.

    This class provides comprehensive details about each stage of the synchronization process,
    including bucket scanning, upload job creation, and processing of individual files.
    """

    status: SyncPrivateDataWithCloudSyncedFolderStatus
    """Overall status of the synchronization job"""

    scan_pages_processing_pending: int
    """Number of bucket listing pages waiting to be processed"""

    scan_pages_processing_done: int
    """Number of bucket listing pages successfully processed"""

    scan_pages_processing_error: int
    """Number of bucket listing pages that failed during processing"""

    scan_pages_processing_cancelled: int
    """Number of bucket listing pages that were canceled during processing"""

    upload_jobs_pending: int
    """Number of upload jobs waiting to be processed"""

    upload_jobs_done: int
    """Number of upload jobs successfully completed"""

    upload_jobs_error: int
    """Number of upload jobs that failed during processing"""

    upload_jobs_units_pending: int
    """Number of individual files waiting to be processed"""

    upload_jobs_units_done: int
    """Number of individual files successfully synchronized"""

    upload_jobs_units_error: int
    """Number of individual files that failed to synchronize"""

    upload_jobs_units_cancelled: int
    """Number of individual files that were canceled during synchronization"""
