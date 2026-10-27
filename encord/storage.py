"""---
title: "Storage"
slug: "sdk-ref-storage"
hidden: false
metadata:
  title: "Storage"
  description: "Encord SDK StorageFolder and StorageItem classes"
category: "64e481b57b6027003f20aaa0"
---
"""

import json
import logging
import mimetypes
import os
import time
import warnings
from dataclasses import dataclass
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Any, Collection, Dict, Iterable, List, Mapping, Optional, Sequence, TextIO, Union
from uuid import UUID

import requests

import encord
import encord.orm.storage as orm_storage
from encord.beta.scene.builder import SceneBuilder
from encord.beta.scene.layout import SceneLayout
from encord.beta.scene.settings import SceneViewSettings
from encord.client import LONG_POLLING_RESPONSE_RETRY_N, LONG_POLLING_SLEEP_ON_FAILURE_SECONDS
from encord.common.deprecated import deprecated
from encord.common.organisation_tags import resolve_organisation_tag_names
from encord.common.utils import snake_to_camel
from encord.exceptions import (
    ClientMetadataPatchPartiallyStartedError,
    ClientMetadataPatchTimeoutError,
    ClientMetadataPatchWaitError,
    EncordException,
)
from encord.http.bundle import Bundle, BundleResultHandler, BundleResultMapper, bundled_operation
from encord.http.constants import DEFAULT_REQUESTS_SETTINGS
from encord.http.utils import (
    CloudUploadSettings,
    UploadPresignedUrlsGetParams,
    _upload_single_file,
    download_signed_urls_as_json,
)
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.base_dto import RootModelDTO, pydantic_version
from encord.orm.dataset import LongPollingStatus
from encord.orm.group import AddStorageFolderGroupsPayload, RemoveGroupsParams, StorageFolderGroup
from encord.orm.project import OrganisationTag
from encord.orm.storage import (
    CustomerProvidedAudioMetadata,
    CustomerProvidedVideoMetadata,
    DataGroupInput,
    DataUploadItems,
    DataUploadTimeSeries,
    FoldersSortBy,
    GetItemParams,
    GetItemsBulkPayload,
    ListItemsParams,
    PatchFolderPayload,
    PatchItemPayload,
    PathElement,
    ReencodeVideoItemsRequest,
    ReencodeVideoItemsResponse,
    StorageFolderSummary,
    StorageFolderType,
    StorageItemSummary,
    StorageItemType,
    StorageLocationName,
    StorageUserRole,
    TimeSeriesViewSettings,
    UploadLongPollingState,
    UploadSignedUrlsPayload,
    _StorageItemPrivateSummary,
    _to_storage_item_summary,
)
from encord.orm.storage import (
    MetadataIngestionConfig as MetadataIngestionConfig,
)
from encord.orm.storage import (
    SidecarMatcherSuffix as SidecarMatcherSuffix,
)
from encord.orm.storage import (
    StorageFolderConfig as StorageFolderConfig,
)
from encord.orm.storage import (
    TimeSeriesLineChannelViewSettings as TimeSeriesLineChannelViewSettings,
)
from encord.orm.storage import (
    TimeSeriesPointsChannelViewSettings as TimeSeriesPointsChannelViewSettings,
)

logger = logging.getLogger(__name__)

STORAGE_BUNDLE_CREATE_LIMIT = 1000
# Polling a client metadata patch job for its result backs off from the first interval to the last.
_CLIENT_METADATA_PATCH_JOB_INITIAL_POLL_SECONDS = 1.0
_CLIENT_METADATA_PATCH_JOB_MAX_POLL_SECONDS = 5.0
# The server rejects a client metadata patch job request whose body is larger than this.
_CLIENT_METADATA_PATCH_JOB_MAX_PAYLOAD_BYTES = 8 * 1024 * 1024
_CLIENT_METADATA_PATCH_JOB_FAILED_MESSAGE = (
    "The job applying this patch failed, or reported a status this SDK version does not recognize; the patch may "
    "have been applied in part."
)


class _NotProvided:
    pass


_NOT_PROVIDED = _NotProvided()


class _ScenePatchItemPayload(PatchItemPayload):
    scene_view_settings: Optional[SceneViewSettings] = None
    scene_layout: Optional[SceneLayout] = None

    def to_dict(self, by_alias=True, exclude_none=True) -> Dict[str, Any]:
        payload = super().to_dict(by_alias=by_alias, exclude_none=exclude_none)
        fields_set = self.model_fields_set if pydantic_version >= 2 else self.__fields_set__
        # Preserve explicit nulls for resettable settings without sending omitted fields.
        for field_name in ("scene_layout", "scene_view_settings", "timeseries_settings"):
            if field_name in fields_set and getattr(self, field_name) is None:
                payload[snake_to_camel(field_name) if by_alias else field_name] = None
        return payload


class StorageFolder:
    """Represents a storage folder within the Encord system."""

    def __init__(self, api_client: ApiClient, orm_folder: orm_storage.StorageFolder):
        self._api_client = api_client
        self._orm_folder = orm_folder
        self._parsed_metadata: Optional[Dict[str, Any]] = None

    @property
    def uuid(self) -> UUID:
        """Gets the unique identifier of the folder.

        Returns:
            UUID: The UUID of the folder.
        """
        return self._orm_folder.uuid

    @property
    def parent_uuid(self) -> Optional[UUID]:
        """Gets the unique identifier of the parent folder.

        Returns:
            Optional[UUID]: The UUID of the parent folder, or None if there is no parent.
        """
        return self._orm_folder.parent

    @property
    def parent(self) -> Optional["StorageFolder"]:
        """Gets the parent folder.

        Returns:
            Optional[StorageFolder]: The parent StorageFolder object, or None if there is no parent.
        """
        parent_uuid = self._orm_folder.parent
        return None if parent_uuid is None else self._get_folder(self._api_client, parent_uuid)

    @property
    def name(self) -> str:
        """Gets the name of the folder.

        Returns:
            str: The name of the folder.
        """
        return self._orm_folder.name

    @property
    def description(self) -> str:
        """Gets the description of the folder.

        Returns:
            str: The description of the folder.
        """
        return self._orm_folder.description

    @property
    def client_metadata(self) -> Optional[Dict[str, Any]]:
        """Gets the client metadata of the folder.

        Returns:
            Optional[Dict[str, Any]]: The client metadata as a dictionary, or None if there is no metadata.
        """
        if self._parsed_metadata is None:
            if self._orm_folder.client_metadata is not None:
                self._parsed_metadata = json.loads(self._orm_folder.client_metadata)
        return self._parsed_metadata

    @property
    def path_to_root(self) -> List[PathElement]:
        """Gets the path elements from the current folder to the root.

        Returns:
            List[PathElement]: A list of PathElement objects representing the path to the root.
        """
        return self._orm_folder.path_to_root

    @property
    def folder_type(self) -> StorageFolderType:
        """Gets the type of the folder.

        Returns:
            StorageFolderType: ``CLOUD_LINKED`` for a cloud-synced folder, ``GENERIC`` for a regular
                folder (see also :attr:`is_cloud_synced`).
        """
        return self._orm_folder.folder_type

    @property
    def is_cloud_synced(self) -> bool:
        """Whether this folder is cloud-synced (mounted on an external bucket via an integration).

        Returns:
            bool: ``True`` if the folder is a cloud-synced (``CLOUD_LINKED``) folder, ``False`` for a
                regular folder.
        """
        return self._orm_folder.folder_type == StorageFolderType.CLOUD_LINKED

    @property
    def integration_hash(self) -> Optional[UUID]:
        """Gets the cloud integration backing this folder.

        Returns:
            Optional[UUID]: The UUID of the cloud integration for a cloud-synced folder, or ``None``
                for a regular folder.
        """
        return self._orm_folder.integration_hash

    @property
    def remote_url(self) -> Optional[str]:
        """Gets the remote bucket/prefix this folder is synced with.

        Returns:
            Optional[str]: The remote URL for a cloud-synced folder, or ``None`` for a regular folder.
        """
        return self._orm_folder.remote_url

    def list_items(
        self,
        *,
        search: Optional[str] = None,
        is_in_dataset: Optional[bool] = None,
        item_types: Optional[List[StorageItemType]] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        get_signed_urls: bool = False,
        include_client_metadata: bool = True,
        resolve_client_metadata_locally: bool = False,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable["StorageItem"]:
        """Lists items in the folder.

        Args:
            search (Optional[str]): Search string to filter items by name.
            is_in_dataset (Optional[bool]): Filter items by whether they are linked to any dataset.
                                            `True` and `False` select only linked and only unlinked items, respectively.
                                            `None` includes all items regardless of their dataset links.
            item_types (Optional[List[StorageItemType]]): Filter items by type.
            order (FoldersSortBy): Sort order. Defaults to FoldersSortBy.NAME.
            get_signed_urls (bool): Whether to get signed URLs for the items. Defaults to False.
            include_client_metadata (bool): Optionally include client metadata into the result of this query.
                Defaults to True.
            resolve_client_metadata_locally (bool): Has no effect unless ``include_client_metadata`` is set.
                When true, the SDK downloads the metadata client-side instead of the server embedding it directly
                in the response. Use this to prevent server timeouts for projects with large client metadata.
            desc (bool): Sort in descending order. Defaults to False.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            Iterable[StorageItem]: Iterable of items in the folder.
        """
        params = ListItemsParams(
            search=search,
            is_in_dataset=is_in_dataset,
            item_types=item_types or [],
            order=order,
            desc=desc,
            page_token=None,
            page_size=page_size,
            sign_urls=get_signed_urls,
            include_client_metadata=include_client_metadata,
            client_metadata_as_signed_url=resolve_client_metadata_locally,
        )

        # Both branches yield a stream of orm StorageItems; the resolve branch additionally in-lines
        # client metadata that the backend returned as signed URLs. A single loop below wraps whatever
        # source we picked, so the two paths never both run.
        if include_client_metadata and resolve_client_metadata_locally:
            orm_items = self._iter_items_resolving_metadata_urls(params)
        else:
            orm_items = self._api_client.get_paged_iterator(
                f"storage/folders/{self.uuid}/items",
                params=params,
                result_type=orm_storage.StorageItem,
            )

        for item in orm_items:
            yield StorageItem(self._api_client, item)

    def _iter_items_resolving_metadata_urls(self, params: ListItemsParams) -> Iterable[orm_storage.StorageItem]:
        """Page through items whose ``client_metadata`` the backend returned as a signed URL, and
        in-line the resolved contents.

        When ``client_metadata_as_signed_url`` is set the backend returns each item's client metadata
        as a signed URL (leaving ``client_metadata`` empty) rather than embedding it, which avoids
        server timeouts for large metadata. We fetch those URLs — batched per page for concurrency —
        and write the decoded JSON back into ``client_metadata`` so callers only ever see resolved
        metadata.
        """
        while True:
            page = self._api_client.get(
                f"storage/folders/{self.uuid}/items",
                params=params,
                result_type=Page[orm_storage.StorageItemWithClientMetadataSignedUrl],
            )

            urls = [item.client_metadata_signed_url for item in page.results if item.client_metadata_signed_url]
            contents_by_url = download_signed_urls_as_json(urls, requests_settings=self._api_client.requests_settings)

            for item in page.results:
                url = item.client_metadata_signed_url
                if url and url in contents_by_url:
                    item.client_metadata = json.dumps(contents_by_url[url])
                yield item

            if page.next_page_token is not None:
                params.page_token = page.next_page_token
            else:
                break

    def delete(self) -> None:
        """Deletes the folder."""
        self._api_client.delete(f"storage/folders/{self.uuid}", params=None, result_type=None)

    def upload_image(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:  # TODO this should return an item?
        """Uploads an image to a folder in Encord storage.

        Args:
            file_path (Union[Path, str]): Path to the image file (e.g., '/home/user/data/image.png').
            title (Optional[str]): The image title. If unspecified, this will be the file name.
            client_metadata (Optional[Dict[str, Any]]): Optional arbitrary metadata to be associated with the image.
                                                        Should be a dictionary that is JSON-serializable.
            cloud_upload_settings (CloudUploadSettings): Settings for uploading data into the cloud. Change this object
                                                        to overwrite the default values.

        Returns:
            UUID: The UUID of the newly created image item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the image could not be uploaded, e.g., due to being in an unsupported format.
        """
        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.IMAGE, count=1, frames_subfolder_name=None
        )
        if len(upload_url_info) != 1:
            raise EncordException("Can't access upload location")

        title = self._guess_title(title, file_path)

        self._upload_local_file(
            file_path,
            title,
            StorageItemType.IMAGE,
            upload_url_info[0].signed_url,
            cloud_upload_settings,
            upload_headers=upload_url_info[0].upload_headers,
        )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                images=[
                    orm_storage.DataUploadImage(
                        object_url=upload_url_info[
                            0
                        ].object_key,  # this is actually ignored when placeholder_item_uuid is set
                        placeholder_item_uuid=upload_url_info[0].item_uuid,
                        title=title,
                        client_metadata=client_metadata or {},
                    )
                ],
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register image, errors occurred {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def upload_video(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        video_metadata: Optional[CustomerProvidedVideoMetadata] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:  # TODO this should return an item?
        """Uploads a video to a folder in Encord storage.

        Args:
            file_path (Union[Path, str]): Path to the video file (e.g., '/home/user/data/video.mp4').
            title (Optional[str]): The video title. If unspecified, this will be the file name. This title should include an extension.
                                For example, "encord_video.mp4".
            client_metadata (Optional[Dict[str, Any]]): Optional arbitrary metadata to be associated with the video.
                                                        Should be a dictionary that is JSON-serializable.
            video_metadata (Optional[CustomerProvidedVideoMetadata]): Optional media metadata for a video file; if provided,
                                                                    Encord service will skip frame synchronization checks and
                                                                    will use the values specified here to render the video
                                                                    in the label editor.
            cloud_upload_settings (CloudUploadSettings): Settings for uploading data into the cloud. Change this object to
                                                        overwrite the default values.

        Returns:
            UUID: The UUID of the newly created video item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the video could not be uploaded, e.g., due to being in an unsupported format.
        """
        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.VIDEO, count=1, frames_subfolder_name=None
        )
        if len(upload_url_info) != 1:
            raise EncordException("Can't access upload location")

        title = self._guess_title(title, file_path)

        self._upload_local_file(
            file_path,
            title,
            StorageItemType.VIDEO,
            upload_url_info[0].signed_url,
            cloud_upload_settings,
            upload_headers=upload_url_info[0].upload_headers,
        )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                videos=[
                    orm_storage.DataUploadVideo(
                        object_url=upload_url_info[
                            0
                        ].object_key,  # this is actually ignored when placeholder_item_uuid is set
                        placeholder_item_uuid=upload_url_info[0].item_uuid,
                        title=title,
                        client_metadata=client_metadata or {},
                        video_metadata=video_metadata,
                    )
                ],
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register video, errors occurred {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def re_encode_videos(self, storage_items: List[UUID], process_title: str, force_full_reencoding: bool) -> UUID:
        """Re-encodes the specified video items.

        Args:
            storage_items (List[UUID]): List of UUIDs representing the video items to be re-encoded.
            process_title (str): Title for the re-encoding process.
            force_full_reencoding (bool): Flag to force full re-encoding.

        Returns:
            UUID: The UUID of the re-encoding process.
        """
        return self._api_client.post(
            "/storage/items/reencode",
            params=None,
            payload=ReencodeVideoItemsRequest(
                storage_items=storage_items,
                process_title=process_title,
                force_full_reencoding=force_full_reencoding,
            ),
            result_type=UUID,
            allow_retries=False,
        )

    def get_re_encoding_status(self, process_hash: UUID) -> ReencodeVideoItemsResponse:
        """Retrieves the status of a re-encoding process.

        Args:
            process_hash (UUID): The UUID of the re-encoding process.

        Returns:
            ReencodeVideoItemsResponse: Response object containing the status of the re-encoding process.
        """
        return self._api_client.get(
            f"/storage/items/reencode/{process_hash}", params=None, result_type=ReencodeVideoItemsResponse
        )

    def create_dicom_series(
        self,
        file_paths: Sequence[Union[str, Path]],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:
        """Uploads a DICOM series to a folder in Encord storage.

        Args:
            file_paths (Sequence[Union[str, Path]]): A list of paths to DICOM files, e.g.,
                ['/home/user/data/DICOM_1.dcm', '/home/user/data/DICOM_2.dcm'].
            title (Optional[str]): The title of the DICOM series. If unspecified, this will be randomly generated.
                This title should NOT include an extension. For example, "encord_image_group".
            client_metadata (Optional[Dict[str, Any]]): Optional arbitrary metadata to be associated with the DICOM series.
                Should be a dictionary that is JSON-serializable.
            cloud_upload_settings (CloudUploadSettings): Settings for uploading data into the cloud. Change this object
                to overwrite the default values.

        Returns:
            UUID: The UUID of the newly created DICOM series item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the series could not be uploaded, e.g., due to being in an unsupported format.
        """
        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.DICOM_FILE, count=len(file_paths), frames_subfolder_name=None
        )
        if len(upload_url_info) != len(file_paths):
            raise EncordException("Can't access upload location")

        dicom_files = []

        for local_file_path, url_info in zip(file_paths, upload_url_info):
            file_title = self._guess_title(None, local_file_path)

            self._upload_local_file(
                local_file_path,
                file_title,
                StorageItemType.DICOM_FILE,
                url_info.signed_url,
                cloud_upload_settings,
                upload_headers=url_info.upload_headers,
            )
            dicom_files.append(
                orm_storage.DataUploadDicomSeriesDicomFile(
                    url=url_info.object_key,  # this is actually ignored when placeholder_item_uuid is set
                    placeholder_item_uuid=url_info.item_uuid,
                    title=file_title,
                )
            )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                dicom_series=[
                    orm_storage.DataUploadDicomSeries(
                        dicom_files=dicom_files,
                        title=title,
                        client_metadata=client_metadata or {},
                    )
                ],
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register DICOM series, errors occurred {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def create_image_group(
        self,
        file_paths: Collection[Union[Path, str]],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:
        """Creates an image group in Encord storage. Choose this type of image upload for non-sequential images that are
        logically connected (for example, multiple views of the same object). See also :meth:`encord.storage.StorageFolder.create_image_sequence`
        and :meth:`encord.storage.StorageFolder.upload_image`.

        Args:
            file_paths (Collection[Union[Path, str]]): A list of paths to images, e.g.,
                ['/home/user/data/img1.png', '/home/user/data/img2.png'].
            title (Optional[str]): The title of the image group. If unspecified, this will be randomly generated.
                This title should NOT include an extension. For example, "encord_image_group".
            client_metadata (Optional[Dict[str, Any]]): Optional arbitrary metadata to be associated with the image group.
                Should be a dictionary that is JSON-serializable.
            cloud_upload_settings (CloudUploadSettings): Settings for uploading data into the cloud. Change this object
                to overwrite the default values.

        Returns:
            UUID: The UUID of the newly created image group item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the images could not be uploaded, e.g., due to being in an unsupported format.
        """
        return self._create_image_group_or_sequence(
            file_paths,
            title,
            create_video=False,
            client_metadata=client_metadata,
            cloud_upload_settings=cloud_upload_settings,
        )

    def create_image_sequence(
        self,
        file_paths: Collection[Union[Path, str]],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:
        """Creates an image sequence in Encord storage. Choose this type of image upload for sequential images (a timelapse
        or similar). A compressed video will be created from the images.

        See also :meth:`encord.storage.StorageFolder.create_image_group` and :meth:`encord.storage.StorageFolder.upload_image`.

        Args:
            file_paths (Collection[Union[Path, str]]): A list of paths to images, e.g.,
                ['/home/user/data/img1.png', '/home/user/data/img2.png'].
            title (Optional[str]): The title of the image sequence. If unspecified, this will be randomly generated.
                This title should NOT include an extension. For example, "front camera 2024-04-01".
            client_metadata (Optional[Dict[str, Any]]): Optional arbitrary metadata to be associated with the image sequence.
                Should be a dictionary that is JSON-serializable.
            cloud_upload_settings (CloudUploadSettings): Settings for uploading data into the cloud. Change this object
                to overwrite the default values.

        Returns:
            UUID: The UUID of the newly created image sequence item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the images could not be uploaded, e.g., due to being in an unsupported format.
        """
        return self._create_image_group_or_sequence(
            file_paths,
            title,
            create_video=True,
            client_metadata=client_metadata,
            cloud_upload_settings=cloud_upload_settings,
        )

    def _create_image_group_or_sequence(
        self,
        file_paths: Collection[Union[Path, str]],
        title: Optional[str],
        create_video: bool,
        client_metadata: Optional[Dict[str, Any]],
        cloud_upload_settings: CloudUploadSettings,
    ) -> UUID:
        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.IMAGE, count=len(file_paths), frames_subfolder_name=None
        )
        if len(upload_url_info) != len(file_paths):
            raise EncordException("Can't access upload location")

        image_group_frames = []

        for local_file_path, url_info in zip(file_paths, upload_url_info):
            file_title = self._guess_title(None, local_file_path)

            self._upload_local_file(
                local_file_path,
                file_title,
                StorageItemType.DICOM_FILE,
                url_info.signed_url,
                cloud_upload_settings,
                upload_headers=url_info.upload_headers,
            )
            image_group_frames.append(
                orm_storage.DataUploadImageGroupImage(
                    url=url_info.object_key,  # this is actually ignored when placeholder_item_uuid is set
                    placeholder_item_uuid=url_info.item_uuid,
                    title=file_title,
                )
            )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                image_groups=[
                    orm_storage.DataUploadImageGroup(
                        images=image_group_frames,
                        title=title,
                        client_metadata=client_metadata or {},
                        create_video=create_video,
                    )
                ],
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register image group, errors occurred {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def upload_nifti(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:
        """
        Uploads a NIfTI file to an Encord Storage Folder.

        Args:
            file_path (Union[Path, str]):
                Path to the local NIfTI file (e.g., '/home/user/data/brain_scan.nii.gz').

            title (Optional[str]):
                Title of the NIfTI item in Encord. If not provided, the filename is used.
                Must include the '.nii' or '.nii.gz' extension.

            client_metadata (Optional[Dict[str, Any]]):
                Custom metadata to associate with the NIfTI file. Must be JSON-serializable.

            cloud_upload_settings (CloudUploadSettings):
                Configuration for how the file is uploaded to the cloud. Use this to override default behavior.

        Returns:
            UUID: UUID of the uploaded NIfTI item.

        Raises:
            AuthorizationError: If the user lacks permission to access the target folder.
            EncordException: If the file cannot be uploaded (for example due to format or metadata issues).
        """

        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.NIFTI, count=1, frames_subfolder_name=None
        )
        if len(upload_url_info) != 1:
            raise EncordException("Can't access upload location")
        title = self._guess_title(title, file_path)

        self._upload_local_file(
            file_path,
            title,
            StorageItemType.NIFTI,
            upload_url_info[0].signed_url,
            cloud_upload_settings,
            upload_headers=upload_url_info[0].upload_headers,
        )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                nifti=[
                    orm_storage.DataUploadNifti(
                        object_url=upload_url_info[
                            0
                        ].object_key,  # this is actually ignored when placeholder_item_uuid is set
                        placeholder_item_uuid=upload_url_info[0].item_uuid,
                        title=title,
                        client_metadata=client_metadata or {},
                    )
                ]
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register nifti, errors occurred {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def upload_audio(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        audio_metadata: Optional[CustomerProvidedAudioMetadata] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:  # TODO this should return an item?
        """Uploads an audio file to an Encord Storage Folder.

        Args:
            file_path (Union[Path, str]):
                Path to the local audio file (e.g., '/home/user/data/audio.mp3').

            title (Optional[str]):
                Title of the audio file in Encord. If not provided, the filename is used.
                The title must include a valid audio file extension (e.g., "encord_audio.mp3").

            client_metadata (Optional[Dict[str, Any]]):
                Custom metadata to associate with the audio. Must be JSON-serializable.

            audio_metadata (Optional[CustomerProvidedAudioMetadata]):
                Optional media metadata describing the audio file. If provided, the Encord skips scanning the file to extract media metadata.

            cloud_upload_settings (CloudUploadSettings):
                Configuration for cloud upload behavior. Override default settings using this parameter.

        Returns:
            UUID: UUID of the uploaded audio item.

        Raises:
            AuthorizationError: If the user is not authorized to access the destination folder.
            EncordException: If the upload fails (for example due to an unsupported audio format).

        #### audio_metadata

        audio_metadata for audio files; if provided, frame synchronization checks are skipped.

        - duration: float - Audio duration in seconds.
        - file_size: int - Size of the audio file in bytes.
        - mime_type: str - MIME type of the audio file (for example: `audio/mpeg` or `audio/wav`).
        - sample_rate: int - Sample rate (int) in Hz.
        - bit_depth: int - Size of each sample (int) in bits.
        - codec: str - Codec (for example: mp3, pcm).
        - num_channels: int - Number of channels.
        """
        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.AUDIO, count=1, frames_subfolder_name=None
        )
        if len(upload_url_info) != 1:
            raise EncordException("Can't access upload location")

        title = self._guess_title(title, file_path)

        self._upload_local_file(
            file_path,
            title,
            StorageItemType.AUDIO,
            upload_url_info[0].signed_url,
            cloud_upload_settings,
            upload_headers=upload_url_info[0].upload_headers,
        )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                audio=[
                    orm_storage.DataUploadAudio(
                        object_url=upload_url_info[
                            0
                        ].object_key,  # this is actually ignored when placeholder_item_uuid is set
                        placeholder_item_uuid=upload_url_info[0].item_uuid,
                        title=title,
                        client_metadata=client_metadata or {},
                        audio_metadata=audio_metadata,
                    )
                ],
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register audio, errors occurred {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def upload_time_series(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        settings: Optional[TimeSeriesViewSettings] = None,
    ) -> UUID:
        """Upload a time-series file to an Encord storage folder.

        Args:
            file_path: Local time-series file to upload, commonly CSV.
            title: Optional item title. Defaults to the local file name.
            client_metadata: Optional JSON-serializable metadata.
            cloud_upload_settings: Retry settings for the file upload.
            settings: Optional initial channel visualization settings.

        Returns:
            UUID of the newly uploaded time-series item.
        """
        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.TIMESERIES, count=1, frames_subfolder_name=None
        )
        if len(upload_url_info) != 1:
            raise EncordException("Can't access upload location")

        title = self._guess_title(title, file_path)
        self._upload_local_file(
            file_path,
            title,
            StorageItemType.TIMESERIES,
            upload_url_info[0].signed_url,
            cloud_upload_settings,
            upload_headers=upload_url_info[0].upload_headers,
        )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                time_series=[
                    DataUploadTimeSeries(
                        object_url=upload_url_info[0].object_key,
                        placeholder_item_uuid=upload_url_info[0].item_uuid,
                        title=title,
                        client_metadata=client_metadata or {},
                        settings=settings,
                    )
                ]
            ),
            ignore_errors=False,
        )
        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register time-series file, errors occurred {upload_result.errors}")
        return upload_result.items_with_names[0].item_uuid

    def upload_text(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        text_metadata: Optional[orm_storage.CustomerProvidedTextMetadata] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:  # TODO this should return an item?
        """Upload a text file to a Folder in Encord storage.

        Args:
            file_path: File path of the text file. For example: '/home/user/data/report.txt'
            title: The item title. If unspecified, the file name is used as the title.
            client_metadata: Optional custom metadata to be associated with the text file. Should be a dictionary that is JSON-serializable.
            text_metadata: Optional media metadata for a text file. The Encord platform uses the specified values instead of scanning the files.
            cloud_upload_settings: Settings for uploading data into the cloud. Change this object to overwrite the default values.

        Returns:
            UUID of the newly created text item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the audio could not be uploaded. For example, due to being in an unsupported format.

        #### text_metadata

        text_metadata for text files. The Encord platform uses the specified values instead of scanning the files.

        - file_size: int - Size of the text file in bytes.
        - mime_type: str - MIME type of the text file (for example: `application/json` or `text/plain`).
        """

        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.PLAIN_TEXT, count=1, frames_subfolder_name=None
        )
        if len(upload_url_info) != 1:
            raise EncordException("Can't access upload location")

        title = self._guess_title(title, file_path)

        self._upload_local_file(
            file_path,
            title,
            StorageItemType.PLAIN_TEXT,
            upload_url_info[0].signed_url,
            cloud_upload_settings,
            upload_headers=upload_url_info[0].upload_headers,
        )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                text=[
                    orm_storage.DataUploadText(
                        object_url=upload_url_info[
                            0
                        ].object_key,  # this is actually ignored when placeholder_item_uuid is set
                        placeholder_item_uuid=upload_url_info[0].item_uuid,
                        title=title,
                        client_metadata=client_metadata or {},
                        text_metadata=text_metadata,
                    )
                ],
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register text file, errors occurred {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def upload_pdf(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        pdf_metadata: Optional[orm_storage.CustomerProvidedPdfMetadata] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:  # TODO this should return an item?
        """Upload a PDF file to a Folder in Encord storage.

        Args:
            file_path: File path of the PDF file. For example: '/home/user/data/report.pdf'
            title: The item title. If unspecified, the file name is used as the title.
            client_metadata: Optional custom metadata to be associated with the PDF file. Should be a dictionary that is JSON-serializable.
            pdf_metadata: Optional media metadata for a PDF file. The Encord platform uses the specified values instead of scanning the files.
            cloud_upload_settings: Settings for uploading data into the cloud. Change this object to overwrite the default values.

        Returns:
            UUID of the newly created PDF item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the document could not be uploaded. For example, due to being in an unsupported format.

        #### pdf_metadata

        pdf_metadata for PDF files. The Encord platform uses the specified values instead of scanning the files.

        - file_size: int - Size of the PDF file in bytes.
        - num_pages: int - Number of pages in the PDF file.
        """
        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.PDF, count=1, frames_subfolder_name=None
        )
        if len(upload_url_info) != 1:
            raise EncordException("Can't access upload location")

        title = self._guess_title(title, file_path)

        self._upload_local_file(
            file_path,
            title,
            StorageItemType.PDF,
            upload_url_info[0].signed_url,
            cloud_upload_settings,
            upload_headers=upload_url_info[0].upload_headers,
        )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                pdf=[
                    orm_storage.DataUploadPDF(
                        object_url=upload_url_info[
                            0
                        ].object_key,  # this is actually ignored when placeholder_item_uuid is set
                        placeholder_item_uuid=upload_url_info[0].item_uuid,
                        title=title,
                        client_metadata=client_metadata or {},
                        pdf_metadata=pdf_metadata,
                    )
                ],
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register text file, errors occurred {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def upload_scene_file(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:
        """Upload a self-contained scene file to Encord-managed storage.

        Supported formats include BAG, DB3, E57, LAS, LAZ, MCAP, PCD, and PLY.

        Args:
            file_path: Path to the local scene file.
            title: Optional item title. Defaults to the local file name.
            client_metadata: Optional JSON-serializable metadata to associate with the scene.
            cloud_upload_settings: Retry settings for the file upload.

        Returns:
            UUID of the newly uploaded scene item.

        Raises:
            EncordException: If the scene format is unsupported or the upload cannot be completed.
        """
        scene_format = Path(file_path).suffix.lower().lstrip(".")
        upload_url_info = self._get_scene_upload_signed_urls(count=1)
        if len(upload_url_info) != 1:
            raise EncordException("Can't access upload location")

        title = self._guess_title(title, file_path)
        self._upload_local_file(
            file_path,
            title,
            StorageItemType.SCENE,
            upload_url_info[0].signed_url,
            cloud_upload_settings,
            upload_headers=upload_url_info[0].upload_headers,
        )

        upload_result = self._add_data(
            integration_id=None,
            private_files=DataUploadItems(
                scenes=[
                    orm_storage.DataUploadScene(
                        title=title,
                        scene={"url": upload_url_info[0].object_key, "format": scene_format},
                        client_metadata=client_metadata or {},
                    )
                ]
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register scene file, errors occurred {upload_result.errors}")
        return upload_result.items_with_names[0].item_uuid

    def upload_scene(
        self,
        scene: SceneBuilder,
        title: str,
        integration_id: str,
        client_metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """Upload a scene to a folder in Encord storage.

        Args:
            scene: Scene builder containing the streams and events to upload.
            title: The scene item title.
            integration_id: UUID of the cloud storage integration that can access the scene asset URIs.
            client_metadata: Optional custom metadata to associate with the scene item.

        Returns:
            UUID of the newly created scene item.

        Raises:
            EncordException: If the scene could not be registered.
        """
        upload_result = self._add_data(
            integration_id=integration_id,
            private_files=DataUploadItems(
                scenes=[
                    orm_storage.DataUploadScene(
                        title=title,
                        scene=scene._build(),
                        client_metadata=client_metadata or {},
                    )
                ],
            ),
            ignore_errors=False,
        )

        if upload_result.status == LongPollingStatus.ERROR:
            raise EncordException(f"Could not register scene, errors occurred {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def add_private_data_to_folder_start(
        self,
        integration_id: str,
        private_files: Union[str, Dict, Path, TextIO, DataUploadItems],
        ignore_errors: bool = False,
    ) -> UUID:
        """Starts the process of adding private data to a folder in Encord storage.

        Args:
            integration_id (str): The integration ID for the folder.
            private_files (Union[str, Dict, Path, TextIO, DataUploadItems]):
                The specification of private files to be added. Can be either a JSON in Encord upload format
                (see the relevant documentation), or an :class:`encord.orm.storage.DataUploadItems` object.
            ignore_errors (bool): If True, errors will be ignored during the upload process.

        Returns:
            UUID: The UUID of the upload job.
        """
        return self._add_data_to_folder_start(integration_id, private_files, ignore_errors)

    def sync_private_data_with_cloud_synced_folder_start(self) -> UUID:
        """Start synchronization of a cloud-synced folder with its remote cloud storage bucket.

        This method triggers a synchronization job that scans the cloud storage bucket linked
        to this folder and updates the Encord storage folder to match. The synchronization is
        performed asynchronously in the background, and this method returns immediately with
        a job UUID that can be used to track the progress.

        The synchronization process:
        1. Scans the cloud bucket for files
        2. Creates new storage items for files that exist in the bucket but not in the folder
        3. Updates the tombstone status of items (marks as tombstone if deleted from bucket,
            restores if re-added)
        4. Updates items if they have the same path but different content (different checksum)

        Returns:
            UUID: The unique identifier for the sync job that can be used with
                 `sync_private_data_with_cloud_synced_folder_get_result` to poll for results.

        Raises:
            InvalidArgumentsError: If the folder is not a cloud-synced folder, or if there are
               permission issues with the cloud storage bucket.

        Note:
            This method can only be used with folders created with cloud_synced_folder_params.
            The SDK process can be terminated after starting the job - the synchronization
            will continue running on the server.
        """

        sync_job_uuid = self._api_client.post(
            path=f"storage/folders/{self.uuid}/cloud-synced-folder-syncs",
            params=None,
            payload=None,
            result_type=UUID,
            allow_retries=False,
        )

        logger.info(f"sync_private_data_with_cloud_synced_folder job started with {sync_job_uuid=}.")
        logger.info("SDK process can be terminated, this will not affect successful job execution.")
        logger.info("You can follow the progress in the web app via notifications.")

        return sync_job_uuid

    def sync_private_data_with_cloud_synced_folder_get_result(
        self,
        sync_job_uuid: UUID,
        timeout_seconds: int = 7 * 24 * 60 * 60,  # 7 days
    ) -> orm_storage.SyncPrivateDataWithCloudSyncedFolderGetResultResponse:
        """Poll for the results of a cloud-synced folder synchronization job.

        This method polls for the status of a synchronization job started with
        `sync_private_data_with_cloud_synced_folder_start()`. It uses long polling to efficiently
        wait for job completion without constantly making API requests. The method returns once
        the job completes or the timeout is reached.

        Args:
            sync_job_uuid (UUID): The UUID of the synchronization job to poll for results.
            timeout_seconds (int): Maximum time in seconds to wait for the job to complete.
                Default is 7 days (604800 seconds).

        Returns:
            SyncPrivateDataWithCloudSyncedFolderGetResultResponse: An object containing the results of
            the synchronization job.

        Raises:
            InvalidArgumentsError: If the synchronization job UUID does not exist or is not associated
                with this folder.

        Note:
            This method will log progress information as it polls for results. For very large
            buckets, the synchronization process can take a significant amount of time.
        """

        failed_requests_count = 0
        polling_start_timestamp = time.perf_counter()

        while True:
            try:
                res = self._api_client.get(
                    f"storage/folders/{self.uuid}/cloud-linked-folder-syncs/{sync_job_uuid}/long-polling",
                    params=orm_storage.SyncPrivateDataWithCloudSyncedFolderGetResultParams(
                        timeout_seconds=timeout_seconds,
                    ),
                    result_type=orm_storage.SyncPrivateDataWithCloudSyncedFolderGetResultResponse,
                )

                if res.status == orm_storage.SyncPrivateDataWithCloudSyncedFolderStatus.DONE:
                    logger.info(f"sync_private_data_with_cloud_synced_folder job completed with {sync_job_uuid=}.")

                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                if (polling_available_seconds == 0) or (
                    res.status
                    in [
                        orm_storage.SyncPrivateDataWithCloudSyncedFolderStatus.DONE,
                        orm_storage.SyncPrivateDataWithCloudSyncedFolderStatus.ERROR,
                        orm_storage.SyncPrivateDataWithCloudSyncedFolderStatus.CANCELLED,
                    ]
                ):
                    return res

                logger.info(
                    f"Sync job status:{res.status.value}, Items syncing progress: (pending:{res.upload_jobs_units_pending}, done:{res.upload_jobs_units_done}, error:{res.upload_jobs_units_error}), "
                    f"Bucket listing pages syncing progress: (pending:{res.scan_pages_processing_pending}, done:{res.scan_pages_processing_done}, error:{res.scan_pages_processing_error}), "
                    f"Created upload jobs statuses: (pending:{res.upload_jobs_pending}, done:{res.upload_jobs_done}, error:{res.upload_jobs_error})"
                )

                failed_requests_count = 0
            except (requests.exceptions.RequestException, encord.exceptions.RequestException):
                failed_requests_count += 1

                if failed_requests_count >= LONG_POLLING_RESPONSE_RETRY_N:
                    raise

                time.sleep(LONG_POLLING_SLEEP_ON_FAILURE_SECONDS)

    def get_folder_config(self) -> orm_storage.StorageFolderConfig:
        """Get the configuration of this storage folder.

        Exposes the optional cloud-synced-folder metadata ingestion configuration
        (``metadata_ingestion``), which is ``None`` unless metadata ingestion has
        been enabled on the folder.

        Returns:
            StorageFolderConfig: The current configuration of the folder.

        See Also:
            :class:`encord.orm.storage.StorageFolderConfig` for the exact set of
            information provided.
        """
        return self._api_client.get(
            f"storage/folders/{self.uuid}/folder-config",
            params=None,
            result_type=orm_storage.StorageFolderConfig,
        )

    def enable_metadata_ingestion(
        self,
        matcher: Optional[orm_storage.SidecarMatcherSuffix] = None,
        *,
        paused: bool = False,
    ) -> None:
        """Enable metadata sidecar ingestion on this cloud-synced folder.

        Reads the current folder config, sets ``metadata_ingestion`` and writes it
        back. Any configuration the SDK does not model is preserved.

        Args:
            matcher (Optional[SidecarMatcherSuffix]): How to identify metadata
                sidecar files. Defaults to a ``.metadata.json`` suffix matcher.
            paused (bool): When ``True``, matched files are claimed as sidecars but
                not attached to data files. Defaults to ``False``.

        Note:
            Requires the API key's user to have the folder-admin role.
        """
        config = self.get_folder_config()
        config.metadata_ingestion = orm_storage.MetadataIngestionConfig(
            matcher=matcher if matcher is not None else orm_storage.SidecarMatcherSuffix(),
            paused=paused,
        )
        self._api_client.post(
            f"storage/folders/{self.uuid}/folder-config",
            params=None,
            payload=config,
            result_type=None,
        )

    def add_private_data_to_folder_get_result(
        self,
        upload_job_id: UUID,
        timeout_seconds: int = 7 * 24 * 60 * 60,  # 7 days
    ) -> UploadLongPollingState:
        """Retrieves the result of adding private data to a folder in Encord storage.

        Args:
            upload_job_id (UUID): The UUID of the upload job.
            timeout_seconds (int): The timeout in seconds for the upload job.

        Returns:
            UploadLongPollingState: The state of the upload job.
        """
        return self._add_data_to_folder_get_result(upload_job_id, timeout_seconds)

    def list_subfolders(
        self,
        *,
        search: Optional[str] = None,
        dataset_synced: Optional[bool] = None,
        organisation_tags_allof: Optional[Union[List[str], List[OrganisationTag]]] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable["StorageFolder"]:
        """Lists subfolders of the current folder.

        Args:
            search (Optional[str]): Search string to filter folders by name.
            dataset_synced (Optional[bool]): Include or exclude folders that are mirrored by a dataset. If `None`,
                no filtering is applied.
            organisation_tags_allof (Optional[Union[List[str], List[OrganisationTag]]]): Optional organisation-tag filter;
                matches only folders tagged with *all* of
                the given tags. Accepts either tag name strings or :class:`encord.orm.project.OrganisationTag`
                instances (as returned by :meth:`encord.user_client.EncordUserClient.list_organisation_tags`).
                Tag names are matched exactly and are case-sensitive. The whole filter is a conjunction, so
                every name must resolve: if any string name is unknown, no folders are listed and a
                :class:`~encord.exceptions.ResourceNotFoundError` naming every unknown tag is raised before the
                folders are listed.
            order (FoldersSortBy): Sort order for the folders. See :class:`encord.orm.storage.FoldersSortBy` for available options.
            desc (bool): If True, sort in descending order.
            page_size (int): Number of folders to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            Iterable[StorageFolder]: An iterable of :class:`encord.storage.StorageFolder` objects.

        Raises:
            ResourceNotFoundError: One or more ``organisation_tags_allof`` names do not match any organization
                tag. The error lists every unknown name.
        """
        return StorageFolder._list_folders(
            self._api_client,
            f"storage/folders/{self.uuid}/folders",
            orm_storage.ListFoldersParams(
                search=search,
                dataset_synced=dataset_synced,
                organisation_tag_names_allof=resolve_organisation_tag_names(self._api_client, organisation_tags_allof),
                order=order,
                desc=desc,
                page_size=page_size,
            ),
        )

    def find_subfolders(
        self,
        search: Optional[str] = None,
        dataset_synced: Optional[bool] = None,
        organisation_tags_allof: Optional[Union[List[str], List[OrganisationTag]]] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable["StorageFolder"]:
        """Recursively searches for storage folders, starting from this folder.

        Args:
            search (Optional[str]): Search string to filter folders by name.
            dataset_synced (Optional[bool]): Include or exclude folders that are mirrored by a dataset. If `None`,
                no filtering is applied.
            organisation_tags_allof (Optional[Union[List[str], List[OrganisationTag]]]): Optional organisation-tag filter;
                matches only folders tagged with *all* of
                the given tags. Accepts either tag name strings or :class:`encord.orm.project.OrganisationTag`
                instances (as returned by :meth:`encord.user_client.EncordUserClient.list_organisation_tags`).
                Tag names are matched exactly and are case-sensitive. The whole filter is a conjunction, so
                every name must resolve: if any string name is unknown, no folders are listed and a
                :class:`~encord.exceptions.ResourceNotFoundError` naming every unknown tag is raised before the
                folders are listed.
            order (FoldersSortBy): Sort order for the folders. See :class:`encord.orm.storage.FoldersSortBy` for available options.
            desc (bool): If True, sort in descending order.
            page_size (int): Number of folders to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            Iterable[StorageFolder]: An iterable of :class:`encord.storage.StorageFolder` objects.

        Raises:
            ResourceNotFoundError: One or more ``organisation_tags_allof`` names do not match any organization
                tag. The error lists every unknown name.
        """
        return StorageFolder._list_folders(
            self._api_client,
            f"storage/folders/{self.uuid}/folders",
            orm_storage.ListFoldersParams(
                search=search,
                is_recursive=True,
                dataset_synced=dataset_synced,
                organisation_tag_names_allof=resolve_organisation_tag_names(self._api_client, organisation_tags_allof),
                order=order,
                desc=desc,
                page_size=page_size,
            ),
        )

    def create_subfolder(
        self,
        name: str,
        description: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
    ) -> "StorageFolder":
        """Create a new subfolder of this folder. See also :meth:`encord.user_client.EncordUserClient.create_storage_folder`.

        Args:
            name: The name of the folder.
            description: The description of the folder.
            client_metadata: Optional arbitrary metadata to be associated with the folder. Should be a dictionary
                that is JSON-serializable.

        Returns:
            The created storage folder. See :class:`encord.storage.StorageFolder` for details.
        """
        return StorageFolder._create_folder(
            api_client=self._api_client,
            name=name,
            description=description,
            client_metadata=client_metadata,
            parent_folder=self,
            cloud_synced_folder_params=None,
        )

    def find_items(
        self,
        search: Optional[str] = None,
        is_in_dataset: Optional[bool] = None,
        item_types: Optional[List[StorageItemType]] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        get_signed_urls: bool = False,
        page_size: int = 100,
    ) -> Iterable["StorageItem"]:
        """Recursively search for storage items, starting from this folder.

        Warning: This method is slow. We recommend using `storage_folder.list_items` instead.

        Args:
            search (Optional[str]): Search string to filter items by name.
            is_in_dataset (Optional[bool]): Filter items by whether they are linked to any dataset. `True` and `False` select
                only linked and only unlinked items, respectively. `None` includes all items regardless of their
                dataset links.
            item_types (Optional[List[StorageItemType]]): Filter items by type.
            order (FoldersSortBy): Sort order.
            desc (bool): Sort in descending order.
            get_signed_urls (bool): If True, return signed URLs for the items.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            Iterable[StorageItem]: An iterable of items in the folder and its subfolders.

        Raises:
            ValueError: If neither `search` nor `item_types` are provided.
        """
        params = ListItemsParams(
            search=search,
            is_recursive=True,
            is_in_dataset=is_in_dataset,
            item_types=item_types or [],
            order=order,
            desc=desc,
            page_token=None,
            page_size=page_size,
            sign_urls=get_signed_urls,
        )

        return StorageFolder._list_items(self._api_client, f"storage/folders/{self.uuid}/items", params)

    def get_summary(self) -> StorageFolderSummary:
        """Get a summary of the folder (total size, number of items, etc).

        Returns:
            StorageFolderSummary: A summary of the folder.

        See Also:
            :class:`encord.orm.storage.StorageFolderSummary` for the exact set of information provided.
        """
        return self._api_client.get(
            f"storage/folders/{self.uuid}/summary",
            params=None,
            result_type=StorageFolderSummary,
        )

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        bundle: Optional[Bundle] = None,
    ) -> None:
        """Update the folder's modifiable properties. Parameters that are not provided  are not updated.

        Args:
            name (Optional[str]): New folder name.
            description (Optional[str]): New folder description.
            client_metadata (Optional[Dict[str, Any]]): New client metadata.
            bundle (Optional[Bundle]): Optional :class:`encord.http.bundle.Bundle` to use for the operation. If provided, the operation is bundled into a single server call with other item updates using the same bundle.

        Returns:
            None
        """
        if name is None and description is None and client_metadata is None:
            return

        if client_metadata is not None:
            self._parsed_metadata = None

        if bundle is not None:
            bundled_operation(
                bundle,
                operation=self._api_client.get_bound_operation(StorageFolder._patch_multiple_folders),
                payload=orm_storage.BundledPatchFolderPayload(
                    folder_patches={
                        str(self.uuid): PatchFolderPayload(
                            name=name,
                            description=description,
                            client_metadata=client_metadata,
                        ),
                    },
                ),
                result_mapper=BundleResultMapper[orm_storage.StorageFolder](
                    result_mapping_predicate=lambda r: str(r.uuid),
                    result_handler=BundleResultHandler(predicate=str(self.uuid), handler=self._set_orm_folder),
                ),
                limit=STORAGE_BUNDLE_CREATE_LIMIT,
            )
        else:
            self._orm_folder = self._api_client.patch(
                f"storage/folders/{self.uuid}",
                params=None,
                payload=PatchFolderPayload(
                    name=name,
                    description=description,
                    client_metadata=client_metadata,
                ),
                result_type=orm_storage.StorageFolder,
            )

    def move_to_folder(self, target_folder: Optional[Union["StorageFolder", UUID]]) -> None:
        """Move the folder to another folder (specify folder object or UUID), or to the root level if `target_folder` is None.

        Args:
            target_folder (Optional[Union[StorageFolder, UUID]]): The target folder to move to, or `None` to move to the root level.

        Returns:
            None
        """
        target_folder_uuid = target_folder.uuid if isinstance(target_folder, StorageFolder) else target_folder
        self._api_client.post(
            "storage/folders/move",
            params=None,
            payload=orm_storage.MoveFoldersPayload(
                folder_uuids=[self.uuid],
                new_parent_uuid=target_folder_uuid,
            ),
            result_type=None,
        )

        self.refetch_data()

    def create_data_group(self, params: Union[DataGroupInput, List[UUID]]) -> UUID:
        """Creates a data group storage item in this folder.

        Args:
            params: Parameters for the data group. Can be:
                - DataGroupInput (DataGroupGrid, DataGroupCarousel, DataGroupCustom): Layout with optional client_metadata
                - List[UUID]: List of item UUIDs (creates a carousel layout)

        Returns:
            UUID: The UUID of the data group storage item.
        """
        return self._create_data_groups([params])[0]

    def create_data_groups(self, params: List[Union[DataGroupInput, List[UUID]]]) -> List[UUID]:
        """Creates multiple data group storage items in this folder.

        Args:
            params: List of parameters for each data group. Each item can be:
                - DataGroupInput (DataGroupGrid, DataGroupCarousel, DataGroupCustom): Layout with optional client_metadata
                - List[UUID]: List of item UUIDs (creates a carousel layout)

        Returns:
            List[UUID]: List of UUIDs of the created data group storage items
        """

        return self._create_data_groups(params)

    def move_items_to_folder(
        self,
        target_folder: Union["StorageFolder", UUID],
        items_to_move: Sequence[Union[UUID, "StorageItem"]],
        allow_mirror_dataset_changes: bool = False,
    ) -> None:
        """Move items (list of `StorageItem` objects or UUIDs) to another folder (specify folder object or UUID).

        Args:
            target_folder (Union[StorageFolder, UUID]): Target folder to move items to.
            items_to_move (Sequence[Union[UUID, StorageItem]]): List of items to move. All the items should be immediate children
                of the current folder.
            allow_mirror_dataset_changes (bool): If `True`, allow moving items that are linked to a mirror dataset. By default,
                moving such items is prohibited, as it would result in data units being removed from a dataset,
                potentially deleting related annotations and other data.

        Returns:
            None
        """
        target_folder_uuid = target_folder if isinstance(target_folder, UUID) else target_folder.uuid

        item_uuids = [item.uuid if isinstance(item, StorageItem) else item for item in items_to_move]
        self._api_client.post(
            f"storage/folders/{self.uuid}/items/move",
            params=None,
            payload=orm_storage.MoveItemsPayload(
                item_uuids=item_uuids,
                new_parent_uuid=target_folder_uuid,
                allow_synced_dataset_move=allow_mirror_dataset_changes,
            ),
            result_type=None,
        )

    def delete_storage_items(self, item_uuids: List[UUID], remove_unused_frames: bool = True) -> None:
        """Delete storage items by their UUIDs.

        Args:
            item_uuids (List[UUID]): List of UUIDs of items to delete. All the items should be immediate children
                of the current folder.
            remove_unused_frames (bool): If `True` (default), remove individual images or DICOM files from image groups or
                DICOM series that are not used in any other item.

        Returns:
            None
        """
        self._api_client.post(
            f"/storage/folders/{self.uuid}/items/delete",
            params=None,
            payload=orm_storage.DeleteItemsPayload(child_uuids=item_uuids, remove_unused_frames=remove_unused_frames),
            result_type=None,  # we don't need a result here, even though the server provides it
        )

    def list_groups(self) -> Iterable[StorageFolderGroup]:
        """List all groups that have access to this folder."""
        page = self._api_client.get(
            f"/storage/folders/{self.uuid}/groups", params=None, result_type=Page[StorageFolderGroup]
        )

        yield from page.results

    def add_group(self, group_hash: Union[List[UUID], UUID], user_role: StorageUserRole):
        """Allow access to this folder for members of a group.

        Args:
            group_hash: Group hash, or a list of group hashes to be added.
            user_role: User role that the group will be given.

        Returns:
            None
        """
        if isinstance(group_hash, UUID):
            group_hash = [group_hash]
        payload = AddStorageFolderGroupsPayload(group_hash_list=group_hash, user_role=user_role)
        self._api_client.post(
            f"/storage/folders/{self.uuid}/groups",
            params=None,
            payload=payload,
            result_type=None,
        )

    def remove_group(self, group_hash: Union[List[UUID], UUID]):
        """Revoke access to the folder from the members of a group.

        Args:
            group_hash: Group hash, or a list of group hashes to be removed.

        Returns:
            None
        """
        if isinstance(group_hash, UUID):
            group_hash = [group_hash]
        params = RemoveGroupsParams(group_hash_list=group_hash)
        self._api_client.delete(f"/storage/folders/{self.uuid}/groups", params=params, result_type=None)

    def refetch_data(self) -> None:
        """Refetch data for the folder.

        Returns:
            None
        """
        self._set_orm_folder(
            self._api_client.get(f"storage/folders/{self.uuid}", params=None, result_type=orm_storage.StorageFolder)
        )

    def _create_data_groups(self, params: List[Union[DataGroupInput, List[UUID]]]) -> List[UUID]:
        group_inputs = [self._normalize_data_group_params(p) for p in params]

        response = self._api_client.post(
            f"storage/folders/{self.uuid}/create-group-items",
            params=None,
            payload=group_inputs,
            result_type=orm_storage.CreateDataGroupsResponse,
        )
        return list(response.root)

    def _set_orm_folder(self, orm_folder: orm_storage.StorageFolder) -> None:
        self._orm_folder = orm_folder

    def _get_upload_signed_urls(
        self, item_type: StorageItemType, count: int, frames_subfolder_name: Optional[str] = None
    ) -> List[orm_storage.UploadSignedUrl]:
        urls = self._api_client.post(
            f"storage/folders/{self.uuid}/upload-signed-urls",
            params=None,
            payload=UploadSignedUrlsPayload(
                item_type=item_type,
                count=count,
                frames_subfolder_name=frames_subfolder_name,
            ),
            result_type=Page[orm_storage.UploadSignedUrl],
        )

        return urls.results

    def _get_scene_upload_signed_urls(self, count: int) -> List[orm_storage.UploadSignedUrl]:
        """Request Encord-hosted upload URLs for self-contained scenes."""
        return self._api_client.get(
            "presigned-urls",
            params=UploadPresignedUrlsGetParams(
                count=count,
                upload_item_type=StorageItemType.SCENE,
            ),
            result_type=Page[orm_storage.UploadSignedUrl],
        ).results

    def _guess_title(self, title: Optional[str], file_path: Union[Path, str]) -> str:
        if title:
            return title

        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.name

    def _get_content_type(self, file_path: Union[Path, str], item_type: StorageItemType) -> str:
        if item_type == StorageItemType.IMAGE:
            return mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        elif item_type == StorageItemType.VIDEO or item_type == StorageItemType.AUDIO:
            return "application/octet-stream"
        elif item_type == StorageItemType.NIFTI:
            return "application/nifti"
        elif item_type == StorageItemType.DICOM_FILE:
            return "application/dicom"
        elif item_type == StorageItemType.PLAIN_TEXT:
            text_mime = mimetypes.guess_type(str(file_path))[0]
            if text_mime and (
                text_mime.startswith("text/")
                or text_mime.startswith("application/json")
                or text_mime.startswith("application/xml")
            ):
                return text_mime
            else:
                raise ValueError(
                    f"Type of {file_path} is detected to be '{text_mime}', which is not supported for text annotations"
                )
        elif item_type == StorageItemType.PDF:
            return "application/pdf"
        elif item_type == StorageItemType.TIMESERIES:
            return mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        elif item_type == StorageItemType.SCENE:
            return "application/octet-stream"
        else:
            raise ValueError(f"Unsupported upload item type `{item_type}`")

    def _upload_local_file(
        self,
        file_path: Union[Path, str],
        title: str,
        item_type: StorageItemType,
        signed_url: str,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        upload_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        content_type = self._get_content_type(file_path, item_type)

        max_retries = (
            cloud_upload_settings.max_retries
            if cloud_upload_settings.max_retries is not None
            else DEFAULT_REQUESTS_SETTINGS.max_retries
        )
        backoff_factor = (
            cloud_upload_settings.backoff_factor
            if cloud_upload_settings.backoff_factor is not None
            else DEFAULT_REQUESTS_SETTINGS.backoff_factor
        )

        _upload_single_file(
            str(file_path),
            title,
            signed_url,
            content_type,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            upload_headers=upload_headers,
        )

    def _add_data(
        self,
        integration_id: Optional[str],
        private_files: Union[str, Dict, Path, TextIO, DataUploadItems],
        ignore_errors: bool = False,
    ) -> orm_storage.UploadLongPollingState:
        upload_job_id = self._add_data_to_folder_start(
            integration_id,
            private_files,
            ignore_errors,
        )

        res = self._add_data_to_folder_get_result(upload_job_id)

        if res.status == LongPollingStatus.DONE:
            return res
        elif res.status == LongPollingStatus.ERROR:
            raise encord.exceptions.EncordException(f"folder.add_data errors occurred {res.errors}")
        else:
            raise ValueError(f"res.status={res.status}, this should never happen")

    def _add_data_to_folder_start(
        self,
        integration_id: Optional[str],
        private_files: Union[str, Dict, Path, TextIO, DataUploadItems],
        ignore_errors: bool = False,
    ) -> UUID:
        file_name: Optional[str] = None
        if isinstance(private_files, dict):
            files: Optional[dict] = private_files
        elif isinstance(private_files, str):
            if os.path.exists(private_files):
                text_contents = Path(private_files).read_text(encoding="utf-8")
                file_name = Path(private_files).name
            else:
                text_contents = private_files

            files = json.loads(text_contents)
        elif isinstance(private_files, Path):
            text_contents = private_files.read_text(encoding="utf-8")
            files = json.loads(text_contents)
            file_name = private_files.name
        elif isinstance(private_files, TextIO):
            text_contents = private_files.read()
            files = json.loads(text_contents)
            file_name = Path(private_files.name).name
        elif isinstance(private_files, DataUploadItems):
            files = None
        else:
            raise ValueError(f"Type [{type(private_files)}] of argument private_files is not supported")

        payload = orm_storage.PostUploadJobParams(
            data_items=private_files if isinstance(private_files, DataUploadItems) else None,
            external_files=files,
            integration_hash=UUID(integration_id) if integration_id is not None else None,
            ignore_errors=ignore_errors,
            file_name=file_name,
        )

        upload_job_id = self._api_client.post(
            path=f"storage/folders/{self.uuid}/data-upload-jobs",
            params=None,
            payload=payload,
            result_type=UUID,
            allow_retries=False,
        )

        logger.info(f"add_data_to_folder job started with upload_job_id={upload_job_id}.")
        logger.info("SDK process can be terminated, this will not affect successful job execution.")
        logger.info("You can follow the progress in the web app via notifications.")

        return upload_job_id

    def _add_data_to_folder_get_result(
        self,
        upload_job_id: UUID,
        timeout_seconds: int = 7 * 24 * 60 * 60,  # 7 days
    ) -> orm_storage.UploadLongPollingState:
        failed_requests_count = 0
        polling_start_timestamp = time.perf_counter()

        while True:
            try:
                res = self._api_client.get(
                    f"storage/folders/{self.uuid}/data-upload-jobs/{upload_job_id}",
                    params=orm_storage.GetUploadJobParams(timeout_seconds=timeout_seconds),
                    result_type=orm_storage.UploadLongPollingState,
                )

                if res.status == LongPollingStatus.DONE:
                    logger.info(f"add_private_data_to_dataset job completed with upload_job_id={upload_job_id}.")

                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                if (polling_available_seconds == 0) or (
                    res.status
                    in [
                        LongPollingStatus.DONE,
                        LongPollingStatus.ERROR,
                        LongPollingStatus.CANCELLED,
                    ]
                ):
                    return res

                files_finished_count = res.units_done_count + res.units_error_count + res.units_cancelled_count
                files_total_count = (
                    res.units_pending_count + res.units_done_count + res.units_error_count + res.units_cancelled_count
                )

                if files_finished_count != files_total_count:
                    logger.info(f"Processed {files_finished_count}/{files_total_count} files")
                else:
                    logger.info("Processed all files, dataset data linking and task creation is performed, please wait")

                failed_requests_count = 0
            except (requests.exceptions.RequestException, encord.exceptions.RequestException):
                failed_requests_count += 1

                if failed_requests_count >= LONG_POLLING_RESPONSE_RETRY_N:
                    raise

                time.sleep(LONG_POLLING_SLEEP_ON_FAILURE_SECONDS)

    def add_data_to_folder_job_cancel(
        self,
        upload_job_id: UUID,
    ) -> orm_storage.AddDataToFolderJobCancelResponse:
        """Cancels a data upload in progress job, associated with this folder.

        Args:
            upload_job_id (UUID): The unique identifier for the upload job.

        Returns:
            AddDataToFolderJobCancelResponse: A response indicating the result of the canceled job.
        """
        return self._api_client.post(
            f"storage/folders/{self.uuid}/data-upload-jobs/{upload_job_id}/cancel",
            params=None,
            payload=None,
            result_type=orm_storage.AddDataToFolderJobCancelResponse,
        )

    @staticmethod
    def _get_folder(api_client: ApiClient, folder_uuid: UUID) -> "StorageFolder":
        orm_folder = api_client.get(
            f"storage/folders/{folder_uuid}", params=None, result_type=orm_storage.StorageFolder
        )
        return StorageFolder(api_client, orm_folder)

    @staticmethod
    def _list_folders(
        api_client: ApiClient,
        path: str,
        params: orm_storage.ListFoldersParams,
    ) -> Iterable["StorageFolder"]:
        if params.page_size < 1 or params.page_size > 1000:
            raise ValueError("page_size should be between 1 and 1000")

        paged_folders = api_client.get_paged_iterator(path, params, orm_storage.StorageFolder)

        for orm_folder in paged_folders:
            yield StorageFolder(api_client, orm_folder)

    @staticmethod
    def _list_items(
        api_client: ApiClient,
        path: str,
        params: orm_storage.ListItemsParams,
    ) -> Iterable["StorageItem"]:
        if params.page_size < 1 or params.page_size > 1000:
            raise ValueError("page_size should be between 1 and 1000")

        if not params.search and not params.item_types:
            raise ValueError("At least one of 'search' or 'item_types' must be provided.")

        paged_items = api_client.get_paged_iterator(path, params, orm_storage.StorageItem)

        for item in paged_items:
            yield StorageItem(api_client, item)

    @staticmethod
    def _patch_multiple_folders(
        api_client: ApiClient,
        folder_patches: Dict[str, PatchFolderPayload],
    ) -> List[orm_storage.StorageFolder]:
        return api_client.patch(
            "storage/folders/patch-bulk",
            params=None,
            payload=orm_storage.PatchFoldersBulkPayload(folder_patches=folder_patches),
            result_type=Page[orm_storage.StorageFolder],
        ).results

    @staticmethod
    def _create_folder(
        api_client: ApiClient,
        name: str,
        description: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        parent_folder: Optional[Union["StorageFolder", UUID]] = None,
        cloud_synced_folder_params: Optional[orm_storage.CloudSyncedFolderParams] = None,
    ) -> "StorageFolder":
        if isinstance(parent_folder, StorageFolder):
            parent_folder = parent_folder.uuid

        payload = orm_storage.CreateStorageFolderPayload(
            name=name,
            description=description,
            parent=parent_folder,
            client_metadata=json.dumps(client_metadata) if client_metadata is not None else None,
            cloud_synced_folder_params=cloud_synced_folder_params,
        )
        folder_orm = api_client.post(
            "storage/folders",
            params=None,
            payload=payload,
            result_type=orm_storage.StorageFolder,
            allow_retries=False,
        )
        return StorageFolder(api_client, folder_orm)

    @staticmethod
    def _normalize_data_group_params(params: Union[DataGroupInput, List[UUID]]) -> DataGroupInput:
        if isinstance(params, list):
            return orm_storage.DataGroupCarousel(layout_contents=params)
        return params


class StorageItemInaccessible:
    def __init__(self, orm_item: orm_storage.StorageItemInaccessible):
        self._orm_item = orm_item

    @property
    def uuid(self) -> UUID:
        """UUID: The unique identifier of the storage item."""
        return self._orm_item.uuid


# A dataclass, not a DTO: the SDK builds it from the jobs it started; it is not parsed from a response.
@dataclass(frozen=True)
class ClientMetadataPatchJobs:
    """The background jobs applying a set of client metadata patches."""

    item_uuids_by_job_uuid: Mapping[UUID, Sequence[UUID]]
    """The items each job patches; check a job with
    :meth:`encord.user_client.EncordUserClient.get_client_metadata_patch_job`."""


def _start_client_metadata_patch_jobs(
    api_client: ApiClient, patches: Dict[UUID, Dict[str, Any]]
) -> Dict[UUID, List[UUID]]:
    """Start jobs for the patches, each within the server's limits on patches and size; returns the items each
    job patches.

    Raises:
        ValueError: A patch is too large to send; no job is started.
        ClientMetadataPatchPartiallyStartedError: Some jobs started, then one could not be. When the first job
            can't be started, its error is raised instead, as nothing is running.
    """
    item_uuids = list(patches)
    # Every group is formed, so a patch too large to send fails, before any job starts.
    groups = [
        group
        for start in range(0, len(item_uuids), STORAGE_BUNDLE_CREATE_LIMIT)
        for group in _split_client_metadata_patches_by_size(
            {item_uuid: patches[item_uuid] for item_uuid in item_uuids[start : start + STORAGE_BUNDLE_CREATE_LIMIT]}
        )
    ]
    item_uuids_by_job_uuid: Dict[UUID, List[UUID]] = {}
    for index, group in enumerate(groups):
        try:
            job_uuid = _create_client_metadata_patch_job(api_client, group)
        except Exception as e:
            if not item_uuids_by_job_uuid:
                raise
            raise ClientMetadataPatchPartiallyStartedError(
                f"Started {len(item_uuids_by_job_uuid)} of {len(groups)} client metadata patch jobs, then could "
                f"not start the next: {e}",
                started=ClientMetadataPatchJobs(item_uuids_by_job_uuid=item_uuids_by_job_uuid),
                not_started_item_uuids=[item_uuid for rest in groups[index:] for item_uuid in rest],
            ) from e
        item_uuids_by_job_uuid[job_uuid] = list(group)
    return item_uuids_by_job_uuid


def _wait_for_client_metadata_patch_jobs(
    api_client: ApiClient, started: ClientMetadataPatchJobs, timeout_seconds: float
) -> List[orm_storage.ClientMetadataPatchResult]:
    """Wait for the jobs until one deadline; returns the patches that could not be confirmed as applied.

    Every item of a job that failed as a whole, or whose status this SDK version does not recognize, is included.

    Raises:
        ClientMetadataPatchTimeoutError: Some jobs are not done when the timeout runs out.
        ClientMetadataPatchWaitError: Checking a job failed before all the jobs were checked.
    """
    deadline = time.monotonic() + timeout_seconds
    failures: List[orm_storage.ClientMetadataPatchResult] = []
    pending_job_uuids: List[UUID] = []
    jobs = list(started.item_uuids_by_job_uuid.items())
    for index, (job_uuid, item_uuids) in enumerate(jobs):
        try:
            job = _poll_client_metadata_patch_job(api_client, job_uuid, deadline)
        except Exception as e:
            unchecked_job_uuids = pending_job_uuids + [rest for rest, _ in jobs[index:]]
            raise ClientMetadataPatchWaitError(
                f"Stopped waiting for {len(unchecked_job_uuids)} of {len(jobs)} client metadata patch jobs: {e}. "
                f"They were not cancelled; check them with EncordUserClient.get_client_metadata_patch_job: "
                f"{unchecked_job_uuids}.",
                pending_job_uuids=unchecked_job_uuids,
                failures=failures,
                started=started,
            ) from e
        if job is None:
            pending_job_uuids.append(job_uuid)
        elif job.status != orm_storage.ClientMetadataPatchJobStatus.DONE:
            failures.extend(
                orm_storage.ClientMetadataPatchResult(
                    item_uuid=item_uuid,
                    status=orm_storage.ClientMetadataPatchStatus.FAILED,
                    error=_CLIENT_METADATA_PATCH_JOB_FAILED_MESSAGE,
                )
                for item_uuid in item_uuids
            )
        else:
            failures.extend(job.failures)
    if pending_job_uuids:
        raise ClientMetadataPatchTimeoutError(
            f"{len(pending_job_uuids)} of {len(jobs)} client metadata patch jobs had not finished "
            f"after {timeout_seconds} seconds: {pending_job_uuids}. They were not cancelled; check them with "
            "EncordUserClient.get_client_metadata_patch_job.",
            pending_job_uuids=pending_job_uuids,
            failures=failures,
            started=started,
        )
    return failures


def _split_client_metadata_patches_by_size(
    patches: Dict[UUID, Dict[str, Any]],
) -> List[Dict[UUID, Dict[str, Any]]]:
    """Group the patches so that each group's job request body stays within the server's size limit.

    Sizes are measured as the request is sent: ``requests`` serializes the body with ``json.dumps``.

    Raises:
        ValueError: A single patch is too large to send.
    """
    envelope_bytes = len(json.dumps(orm_storage.CreateClientMetadataPatchJobPayload(patches=[]).to_dict()))
    groups: List[Dict[UUID, Dict[str, Any]]] = []
    group: Dict[UUID, Dict[str, Any]] = {}
    group_bytes = envelope_bytes
    for item_uuid, patch in patches.items():
        entry = orm_storage.ClientMetadataPatch(item_uuid=item_uuid, merge_patch=patch).to_dict()
        # Entries are joined with ", ".
        entry_bytes = len(json.dumps(entry)) + 2
        if envelope_bytes + entry_bytes > _CLIENT_METADATA_PATCH_JOB_MAX_PAYLOAD_BYTES:
            raise ValueError(f"The client metadata patch for item {item_uuid} is too large to send.")
        if group and group_bytes + entry_bytes > _CLIENT_METADATA_PATCH_JOB_MAX_PAYLOAD_BYTES:
            groups.append(group)
            group, group_bytes = {}, envelope_bytes
        group[item_uuid] = patch
        group_bytes += entry_bytes
    if group:
        groups.append(group)
    return groups


def _create_client_metadata_patch_job(api_client: ApiClient, patches: Dict[UUID, Dict[str, Any]]) -> UUID:
    return api_client.post(
        "storage/items/client-metadata/patch-jobs",
        params=None,
        payload=orm_storage.CreateClientMetadataPatchJobPayload(
            patches=[
                orm_storage.ClientMetadataPatch(item_uuid=item_uuid, merge_patch=patch)
                for item_uuid, patch in patches.items()
            ]
        ),
        result_type=orm_storage.CreateClientMetadataPatchJobResponse,
        # A retry after the job was started would start a second job for the same patches.
        allow_retries=False,
    ).job_uuid


def _poll_client_metadata_patch_job(
    api_client: ApiClient, job_uuid: UUID, deadline: float
) -> Optional[orm_storage.ClientMetadataPatchJobResult]:
    """Poll the job until it is done or has failed, or the deadline passes; None if it is still running then.

    The job is checked at least once, even when the deadline has already passed.
    """
    interval = _CLIENT_METADATA_PATCH_JOB_INITIAL_POLL_SECONDS
    while True:
        job = api_client.get(
            f"storage/items/client-metadata/patch-jobs/{job_uuid}",
            params=None,
            result_type=orm_storage.ClientMetadataPatchJobResult,
        )
        if job.status != orm_storage.ClientMetadataPatchJobStatus.PENDING:
            return job
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        time.sleep(min(interval, remaining))
        interval = min(interval * 2, _CLIENT_METADATA_PATCH_JOB_MAX_POLL_SECONDS)


@dataclass(frozen=True)
class ClientMetadataPatchJobsByUrl(ClientMetadataPatchJobs):
    """The background jobs applying client metadata patches by object URL, and the items found for each URL."""

    item_uuids_by_url: Dict[str, List[UUID]]
    """The items found for each object URL; empty for a URL that matches no item."""


@dataclass(frozen=True)
class ClientMetadataPatchByUrlResult:
    """The items found for each object URL, and the patches that could not be confirmed as applied to them."""

    item_uuids_by_url: Dict[str, List[UUID]]
    """The items found for each object URL; empty for a URL that matches no item."""
    failures: List[orm_storage.ClientMetadataPatchResult]
    """The patches that could not be confirmed as applied, with the reason where available."""


def _lookup_items_by_url(
    api_client: ApiClient, object_urls: List[str], folder_uuids: Optional[List[UUID]]
) -> Dict[str, List[UUID]]:
    """The items with each object URL, directly in the folders or anywhere in the organization, leaving out those
    in cloud synced folders; an empty list for a URL that matches no such item."""
    item_uuids_by_url: Dict[str, List[UUID]] = {url: [] for url in object_urls}
    for start in range(0, len(object_urls), STORAGE_BUNDLE_CREATE_LIMIT):
        payload = orm_storage.LookupItemsByUrlPayload(
            object_urls=object_urls[start : start + STORAGE_BUNDLE_CREATE_LIMIT],
            folder_uuids=folder_uuids,
            # Their client metadata can't be patched, and a job with any of them is rejected.
            include_cloud_synced=False,
        )
        params = orm_storage.LookupItemsByUrlParams()
        while True:
            page = api_client.post(
                "storage/items/lookup-by-url",
                params=params,
                payload=payload,
                result_type=Page[orm_storage.ItemUrlMatch],
            )
            for match in page.results:
                item_uuids_by_url[match.object_url].append(match.item_uuid)
            if page.next_page_token is None:
                break
            params = orm_storage.LookupItemsByUrlParams(page_token=page.next_page_token)
    return item_uuids_by_url


def _start_client_metadata_patch_jobs_by_url(
    api_client: ApiClient, patches: Dict[str, Dict[str, Any]], folder_uuids: Optional[List[UUID]]
) -> ClientMetadataPatchJobsByUrl:
    if folder_uuids is not None and not folder_uuids:
        raise ValueError("`folders` is empty; omit it to look in the whole organisation.")
    if "" in patches:
        raise ValueError("An object URL in `patches` is empty.")
    item_uuids_by_url = _lookup_items_by_url(api_client, list(patches), folder_uuids)
    patch_by_item_uuid = {
        item_uuid: patches[url] for url, item_uuids in item_uuids_by_url.items() for item_uuid in item_uuids
    }
    try:
        item_uuids_by_job_uuid = _start_client_metadata_patch_jobs(api_client, patch_by_item_uuid)
    except ClientMetadataPatchPartiallyStartedError as e:
        # The same error, with the items found for each URL too.
        raise ClientMetadataPatchPartiallyStartedError(
            e.message,
            started=ClientMetadataPatchJobsByUrl(
                item_uuids_by_job_uuid=e.started.item_uuids_by_job_uuid, item_uuids_by_url=item_uuids_by_url
            ),
            not_started_item_uuids=e.not_started_item_uuids,
        ) from e.__cause__
    return ClientMetadataPatchJobsByUrl(
        item_uuids_by_job_uuid=item_uuids_by_job_uuid, item_uuids_by_url=item_uuids_by_url
    )


class StorageItem:
    def __init__(self, api_client: ApiClient, orm_item: orm_storage.StorageItem):
        self._api_client = api_client
        self._orm_item = orm_item
        self._parsed_metadata: Optional[Dict[str, Any]] = None

    @property
    def uuid(self) -> UUID:
        """UUID: The unique identifier of the storage item."""
        return self._orm_item.uuid

    @property
    def parent_folder_uuid(self) -> UUID:
        """UUID: The UUID of the parent folder."""
        return self._orm_item.parent

    def parent_folder(self) -> StorageFolder:
        """Retrieve the parent folder of the storage item.

        Returns:
            StorageFolder: The parent folder.
        """
        return StorageFolder._get_folder(self._api_client, self.parent_folder_uuid)

    @property
    def item_type(self) -> StorageItemType:
        """StorageItemType: The type of the storage item."""
        return self._orm_item.item_type

    @property
    def name(self) -> str:
        """str: The name of the storage item."""
        return self._orm_item.name

    @property
    @deprecated(version="0.1.177")
    def description(self) -> str:
        """str: This is always an empty string; descriptions on individual items are not supported."""
        return self._orm_item.description

    @property
    def client_metadata(self) -> Optional[Dict[str, Any]]:
        """Optional[Dict[str, Any]]: The client metadata of the storage item."""
        if self._parsed_metadata is None:
            if self._orm_item.client_metadata is not None:
                self._parsed_metadata = json.loads(self._orm_item.client_metadata)
        return self._parsed_metadata

    @property
    def timeseries_settings(self) -> Optional[TimeSeriesViewSettings]:
        """Optional persisted visualization settings for a time-series item."""
        return self._orm_item.timeseries_settings

    @property
    def created_at(self) -> datetime:
        """datetime: The creation time of the storage item."""
        return self._orm_item.created_at

    @property
    def last_edited_at(self) -> datetime:
        """datetime: The last edited time of the storage item."""
        return self._orm_item.last_edited_at

    @property
    def backed_data_units_count(self) -> int:
        """int: The number of backed data units."""
        return self._orm_item.backed_data_units_count

    @property
    def storage_location(self) -> StorageLocationName:
        """StorageLocationName: The storage location name."""
        return self._orm_item.storage_location

    @property
    def integration_hash(self) -> Optional[UUID]:
        """Optional[UUID]: The integration hash."""
        return self._orm_item.integration_hash

    @property
    def url(self) -> Optional[str]:
        """Optional[str]: The URL of the storage item."""
        return self._orm_item.url

    @property
    def file_size(self) -> Optional[int]:
        """Optional[int]: The file size of the storage item."""
        return self._orm_item.file_size

    @property
    def mime_type(self) -> Optional[str]:
        """Optional[str]: The MIME type of the storage item."""
        return self._orm_item.mime_type

    @property
    def duration(self) -> Optional[float]:
        """Optional[float]: The duration of the storage item."""
        return self._orm_item.duration

    @property
    def fps(self) -> Optional[float]:
        """Optional[float]: The frames per second of the storage item."""
        return self._orm_item.fps

    @property
    def height(self) -> Optional[int]:
        """Optional[int]: The height of the storage item."""
        return self._orm_item.height

    @property
    def width(self) -> Optional[int]:
        """Optional[int]: The width of the storage item."""
        return self._orm_item.width

    @property
    def dicom_instance_uid(self) -> Optional[str]:
        """Optional[str]: The DICOM instance UID of the storage item."""
        return self._orm_item.dicom_instance_uid

    @property
    def dicom_study_uid(self) -> Optional[str]:
        """Optional[str]: The DICOM study UID of the storage item."""
        return self._orm_item.dicom_study_uid

    @property
    def dicom_series_uid(self) -> Optional[str]:
        """Optional[str]: The DICOM series UID of the storage item."""
        return self._orm_item.dicom_series_uid

    @property
    def frame_count(self) -> Optional[int]:
        """Optional[int]: The frame count of the storage item."""
        return self._orm_item.frame_count

    @property
    def audio_sample_rate(self) -> Optional[int]:
        """Optional[int]: The number of samples taken per second (in Hz)."""
        return self._orm_item.audio_sample_rate

    @property
    def audio_bit_depth(self) -> Optional[int]:
        """Optional[int]: The number of bits used to record each audio sample."""
        return self._orm_item.audio_bit_depth

    @property
    def audio_codec(self) -> Optional[str]:
        """Optional[int]: The codec of the audio file (e.g., mp3 or flac)."""
        return self._orm_item.audio_codec

    @property
    def audio_num_channels(self) -> Optional[int]:
        """Optional[int]: The number of channels."""
        return self._orm_item.audio_num_channels

    def get_signed_url(self, refetch: bool = False) -> Optional[str]:
        """Get a signed URL for downloading the item.

        Returns `None` for composite items that have no single file URL:
        - For scenes, use :class:`encord.beta.scene.SceneReader` to get signed URLs for all constituent files.
        - For image groups and DICOM series, use :meth:`get_child_items` to get signed URLs for individual frames.

        Args:
            refetch: If `True`, forces fetching a new signed URL even if one is cached.

        Returns:
            Optional[str]: Signed URL for downloading the item, or `None` for composite items.
        """
        if self.item_type in {StorageItemType.SCENE, StorageItemType.DICOM_SERIES, StorageItemType.IMAGE_GROUP}:
            warnings.warn(
                f"get_signed_url() is not supported for {self.item_type} items and will raise ValueError in a future "
                f"version. Use SceneReader(item) for scenes, or get_child_items() for image groups and DICOM series.",
                DeprecationWarning,
                stacklevel=2,
            )
            return None

        if refetch or self._orm_item.signed_url is None:
            self.refetch_data(get_signed_url=True)

        return self._orm_item.signed_url

    def get_summary(self) -> StorageItemSummary:
        """Retrieve a summary of the item, including linked datasets and other information.

        Returns:
            StorageItemSummary: Object containing summary information about the item.
        """
        return _to_storage_item_summary(
            self._api_client.get(
                f"storage/folders/{self.parent_folder_uuid}/items/{self.uuid}/summary",
                params=orm_storage._GetItemSummaryParams(include_group_layout=True),
                result_type=_StorageItemPrivateSummary,
            )
        )

    def get_child_items(self, get_signed_urls: bool = False) -> Iterable["StorageItem"]:
        """Get child items of the item, such as frames of an image group or files of DICOM series.

        Args:
            get_signed_urls: If `True`, include signed URLs for child items.

        Returns:
            Iterable[StorageItem]: List of child items accessible to the user.
        """
        if self.item_type not in {
            StorageItemType.IMAGE_GROUP,
            StorageItemType.GROUP,
            StorageItemType.IMAGE_SEQUENCE,
            StorageItemType.DICOM_SERIES,
        }:
            return []

        child_items = self._api_client.get(
            f"/storage/folders/{self.parent_folder_uuid}/items/{self.uuid}/child-items",
            params=orm_storage.GetChildItemsParams(sign_urls=get_signed_urls),
            result_type=Page[orm_storage.StorageItem],
        ).results

        return [StorageItem(self._api_client, item) for item in child_items]

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        timeseries_settings: Union[TimeSeriesViewSettings, None, _NotProvided] = _NOT_PROVIDED,
        bundle: Optional[Bundle] = None,
        scene_view_settings: Union[SceneViewSettings, None, _NotProvided] = _NOT_PROVIDED,
        scene_layout: Union[SceneLayout, None, _NotProvided] = _NOT_PROVIDED,
    ) -> None:
        """Update modifiable properties of the item.

        Args:
            name: New item name.
            description: New item description.
            client_metadata: New client metadata.
            timeseries_settings: New time-series channel visualization settings. Pass None to restore defaults;
                omit to leave the existing settings unchanged.
            bundle: Optional :class:`encord.http.bundle.Bundle` to use for the operation. If provided, the operation
            scene_view_settings: New scene visualization settings. Pass None to restore defaults;
                omit to leave the existing settings unchanged.
            scene_layout: New scene tile and timeline layout. Pass None to remove the layout;
                omit to leave the existing layout unchanged.

        Returns:
            None

        Notes:
            If no parameters are provided, the function does nothing.

            If `bundle` is provided, the operation is bundled into a single server call with other item updates
            using the same bundle.
        """
        if (
            name is None
            and description is None
            and client_metadata is None
            and isinstance(timeseries_settings, _NotProvided)
            and isinstance(scene_view_settings, _NotProvided)
            and isinstance(scene_layout, _NotProvided)
        ):
            return

        if client_metadata is not None:
            self._parsed_metadata = None
        payload = _ScenePatchItemPayload(
            name=name,
            description=description,
            client_metadata=client_metadata,
        )
        if not isinstance(timeseries_settings, _NotProvided):
            payload.timeseries_settings = timeseries_settings
        if not isinstance(scene_view_settings, _NotProvided):
            payload.scene_view_settings = scene_view_settings
        if not isinstance(scene_layout, _NotProvided):
            payload.scene_layout = scene_layout

        if bundle is not None:
            bundled_operation(
                bundle,
                operation=self._api_client.get_bound_operation(StorageItem._patch_multiple_items),
                payload=orm_storage.BundledPatchItemPayload(
                    item_patches={str(self.uuid): payload},
                ),
                result_mapper=BundleResultMapper[orm_storage.StorageItem](
                    result_mapping_predicate=lambda r: str(r.uuid),
                    result_handler=BundleResultHandler(predicate=str(self.uuid), handler=self._set_orm_item),
                ),
                limit=STORAGE_BUNDLE_CREATE_LIMIT,
            )
        else:
            self._orm_item = self._api_client.patch(
                f"storage/folders/{self.parent_folder_uuid}/items/{self.uuid}",
                params=None,
                payload=payload,
                result_type=orm_storage.StorageItem,
            )

    def patch_client_metadata(self, patch: Dict[str, Any]) -> None:
        """Change some of the item's client metadata keys, leaving all other keys as they are.

        ``patch`` is applied as an `RFC 7396 <https://www.rfc-editor.org/rfc/rfc7396>`_ JSON merge patch:

        - A key with a value adds the key, or replaces its current value.
        - A key with ``None`` removes the key.
        - A dict value is merged into the current dict value by the same rules.
        - Any other value, including a list, replaces the current value as a whole.

        Keys not included in ``patch`` are left unchanged.
        After the call, :attr:`client_metadata` holds the merged metadata; a patch refused with one of the errors
        below changes nothing. To replace the whole client metadata, use :meth:`update` instead.

        Example:
            ``item.patch_client_metadata({"reviewed": True, "camera": {"fps": 60}, "draft": None})``
            sets ``reviewed``, sets ``camera.fps`` while keeping the other ``camera`` keys, and removes ``draft``.

        Args:
            patch: The keys to add, change or remove.

        Returns:
            None

        Raises:
            :class:`encord.exceptions.AuthorisationError`: The item does not exist or you cannot edit it.
            :class:`encord.exceptions.InvalidArgumentsError`: The patch can't be applied, for example because the item
                is in a cloud synced folder or the merged metadata would be too large.
            :class:`encord.exceptions.ResourceExistsError`: Other changes to the item's client metadata kept
                conflicting with the patch (retry), or its current client metadata can't be read (replace it with
                :meth:`update`).
        """
        merged = self._api_client.patch(
            f"storage/items/{self.uuid}/client-metadata",
            params=None,
            payload=RootModelDTO[Dict[str, Any]](patch),  # type: ignore[arg-type]
            result_type=RootModelDTO[Dict[str, Any]],
            content_type="application/merge-patch+json",
        )
        self._orm_item.client_metadata = json.dumps(merged.root)
        self._parsed_metadata = None

    def delete(self, remove_unused_frames=True) -> None:
        """Delete the item from the storage.

        Args:
            remove_unused_frames: If `True` (default), remove individual images or DICOM files not used elsewhere.

        Returns:
            None
        """
        self._api_client.post(
            f"/storage/folders/{self.parent_folder_uuid}/items/delete",
            params=None,
            payload=orm_storage.DeleteItemsPayload(child_uuids=[self.uuid], remove_unused_frames=remove_unused_frames),
            result_type=None,  # we don't need a result here, even though the server provides it
        )

    def move_to_folder(
        self,
        target_folder: Union[StorageFolder, UUID],
        allow_mirror_dataset_changes: bool = False,
    ) -> None:
        """Move the item to another folder.

        Args:
            target_folder: Target folder to move the item to. Can be a `StorageFolder` object or a UUID.
            allow_mirror_dataset_changes: If `True`, allows moving items linked to a mirror dataset.
                Default is `False`, which prohibits such moves to prevent data loss.

        Returns:
            None

        Notes:
            This method updates the item's parent folder and refetches item data after the move.
        """
        target_folder_uuid = target_folder if isinstance(target_folder, UUID) else target_folder.uuid
        self._api_client.post(
            f"storage/folders/{self.parent_folder_uuid}/items/move",
            params=None,
            payload=orm_storage.MoveItemsPayload(
                item_uuids=[self.uuid],
                new_parent_uuid=target_folder_uuid,
                allow_synced_dataset_move=allow_mirror_dataset_changes,
            ),
            result_type=None,
        )
        self.refetch_data()

    def refetch_data(self, get_signed_url: bool = False) -> None:
        """Refetches data for the item, updating its attributes.

        Args:
            get_signed_url: If `True`, refetches the signed URL for downloading the item.

        Returns:
            None
        """
        self._set_orm_item(
            self._api_client.get(
                f"storage/items/{self.uuid}",
                params=GetItemParams(sign_url=get_signed_url),
                result_type=orm_storage.StorageItem,
            )
        )

    @staticmethod
    def _get_item(api_client: ApiClient, item_uuid: UUID, get_signed_url: bool) -> "StorageItem":
        orm_item = api_client.get(
            f"storage/items/{item_uuid}",
            params=GetItemParams(sign_url=get_signed_url),
            result_type=orm_storage.StorageItem,
        )
        return StorageItem(api_client, orm_item)

    @staticmethod
    def _get_items(api_client: ApiClient, item_uuids: List[UUID], get_signed_url: bool) -> List["StorageItem"]:
        orm_items = api_client.post(
            "storage/items/get-bulk",
            params=None,
            payload=GetItemsBulkPayload(item_uuids=item_uuids, sign_urls=get_signed_url),
            result_type=Page[orm_storage.StorageItem],
        )
        return [StorageItem(api_client, orm_item) for orm_item in orm_items.results]

    @staticmethod
    def _get_items_bulk(
        api_client: ApiClient, item_uuids: List[UUID], get_signed_url: bool
    ) -> List[orm_storage.StorageItem]:
        return api_client.post(
            "storage/items/get-bulk",
            params=None,
            payload=GetItemsBulkPayload(item_uuids=item_uuids, sign_urls=get_signed_url),
            result_type=Page[orm_storage.StorageItem],
        ).results

    @staticmethod
    def _patch_multiple_items(
        api_client: ApiClient,
        item_patches: Dict[str, PatchItemPayload],
    ) -> List[orm_storage.StorageItem]:
        return api_client.patch(
            "storage/items/patch-bulk",
            params=None,
            payload=orm_storage.PatchItemsBulkPayload(item_patches=item_patches),
            result_type=Page[orm_storage.StorageItem],
        ).results

    def _set_orm_item(self, orm_item: orm_storage.StorageItem) -> None:
        self._orm_item = orm_item
        self._parsed_metadata = None
