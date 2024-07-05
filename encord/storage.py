"""
---
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
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Any, Collection, Dict, Iterable, List, Optional, Sequence, TextIO, Union
from uuid import UUID

import requests

import encord
import encord.orm.storage as orm_storage
from encord.client import LONG_POLLING_RESPONSE_RETRY_N, LONG_POLLING_SLEEP_ON_FAILURE_SECONDS
from encord.exceptions import EncordException
from encord.http.bundle import Bundle, BundleResultHandler, BundleResultMapper, bundled_operation
from encord.http.constants import DEFAULT_REQUESTS_SETTINGS
from encord.http.utils import CloudUploadSettings, _upload_single_file
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.dataset import LongPollingStatus
from encord.orm.storage import (
    CustomerProvidedVideoMetadata,
    DataUploadItems,
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
    StorageItemSummary,
    StorageItemType,
    UploadSignedUrlsPayload,
)

logger = logging.getLogger(__name__)

STORAGE_BUNDLE_CREATE_LIMIT = 1000


class StorageFolder:
    def __init__(self, api_client: ApiClient, orm_folder: orm_storage.StorageFolder):
        self._api_client = api_client
        self._orm_folder = orm_folder
        self._parsed_metadata: Optional[Dict[str, Any]] = None

    @property
    def uuid(self) -> UUID:
        return self._orm_folder.uuid

    @property
    def parent_uuid(self) -> Optional[UUID]:
        return self._orm_folder.parent

    @property
    def parent(self) -> Optional["StorageFolder"]:
        parent_uuid = self._orm_folder.parent
        return None if parent_uuid is None else self._get_folder(self._api_client, parent_uuid)

    @property
    def name(self) -> str:
        return self._orm_folder.name

    @property
    def description(self) -> str:
        return self._orm_folder.description

    @property
    def client_metadata(self) -> Optional[Dict[str, Any]]:
        if self._parsed_metadata is None:
            if self._orm_folder.client_metadata is not None:
                self._parsed_metadata = json.loads(self._orm_folder.client_metadata)
        return self._parsed_metadata

    @property
    def path_to_root(self) -> List[PathElement]:
        return self._orm_folder.path_to_root

    def list_items(
        self,
        *,
        search: Optional[str] = None,
        is_in_dataset: Optional[bool] = None,
        item_types: Optional[List[StorageItemType]] = None,
        order: orm_storage.FoldersSortBy = orm_storage.FoldersSortBy.NAME,
        get_signed_urls: bool = False,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable["StorageItem"]:
        """
        List items in the folder.

        Args:
            search: Search string to filter items by name.
            is_in_dataset: Filter items by whether they are linked to any dataset. `True` and `False` select
                only linked and only unlinked items, respectively. `None` includes all items regardless of their
                dataset links.
            item_types: Filter items by type.
            order: Sort order.
            desc: Sort in descending order.
            page_size: Number of items to return per page.

        Returns:
            Iterable of items in the folder.
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
        )

        paged_items = self._api_client.get_paged_iterator(
            f"storage/folders/{self.uuid}/items",
            params=params,
            result_type=orm_storage.StorageItem,
        )

        for item in paged_items:
            yield StorageItem(self._api_client, item)

    def delete(self) -> None:
        self._api_client.delete(f"storage/folders/{self.uuid}", params=None, result_type=None)

    def upload_image(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:  # TODO this should return an item?
        """
        Upload image to a folder in Encord storage.

        Args:
            file_path: path to image e.g. '/home/user/data/image.png'
            title:
                The image title. If unspecified, this will be the file name.
            client_metadata:
                Optional arbitrary metadata to be associated with the image. Should be a dictionary
                that is JSON-serializable.
            cloud_upload_settings:
                Settings for uploading data into the cloud. Change this object to overwrite the default values.

        Returns:
            UUID of the newly created image item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the image could not be uploaded, e.g. due to being in an unsupported format.
        """
        upload_url_info = self._get_upload_signed_urls(
            item_type=StorageItemType.IMAGE, count=1, frames_subfolder_name=None
        )
        if len(upload_url_info) != 1:
            raise EncordException("Can't access upload location")

        title = self._guess_title(title, file_path)

        self._upload_local_file(
            file_path, title, StorageItemType.IMAGE, upload_url_info[0].signed_url, cloud_upload_settings
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
            raise EncordException(f"Could not register image, errors occured {upload_result.errors}")
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
        """
        Upload video to a folder in Encord storage.

        Args:
            file_path: path to video e.g. '/home/user/data/video.mp4'
            title:
                The video title. If unspecified, this will be the file name. This title should include an extension.
                For example "encord_video.mp4".
            client_metadata:
                Optional arbitrary metadata to be associated with the video. Should be a dictionary
                that is JSON-serializable.
            video_metadata:
                Optional media metadata for a video file; if provided, Encord service will skip frame
                synchronisation checks and will use the values specified here to render the video in the label editor.
            cloud_upload_settings:
                Settings for uploading data into the cloud. Change this object to overwrite the default values.

        Returns:
            UUID of the newly created video item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the video could not be uploaded, e.g. due to being in an unsupported format.
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
            raise EncordException(f"Could not register video, errors occured {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def re_encode_videos(self, storage_items: List[UUID], process_title: str, force_full_reencoding: bool) -> UUID:
        return self._api_client.post(
            "/storage/items/reencode",
            params=None,
            payload=ReencodeVideoItemsRequest(
                storage_items=storage_items,
                process_title=process_title,
                force_full_reencoding=force_full_reencoding,
            ),
            result_type=UUID,
        )

    def get_re_encoding_status(self, process_hash: UUID) -> ReencodeVideoItemsResponse:
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
        """
        Upload a DICOM series to a folder in Encord storage.

        Args:
            file_paths: a list of paths to DICOM files, e.g.
                ['/home/user/data/DICOM_1.dcm', '/home/user/data/DICOM_2.dcm']
            title:
                The title of the DICOM series. If unspecified this will be randomly generated for you. This title should
                NOT include an extension. For example "encord_image_group".
            client_metadata:
                Optional arbitrary metadata to be associated with the video. Should be a dictionary
                that is JSON-serializable.
            cloud_upload_settings:
                Settings for uploading data into the cloud. Change this object to overwrite the default values.

        Returns:
            UUID of the newly created DICOM series item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the series could not be uploaded, e.g. due to being in an unsupported format.
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
            raise EncordException(f"Could not register DICOM series, errors occured {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def create_image_group(
        self,
        file_paths: Collection[Union[Path, str]],
        title: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> UUID:
        """
        Create an image group in Encord storage. Choose this type of image upload for non-sequential images that are
        logically connected (e.g. multiple views of the same object). See also :meth:`.Folder.create_image_sequence`
        and :meth:`.Folder.upload_image`.

        Args:
            file_paths: a list of paths to images, e.g.
                ['/home/user/data/img1.png', '/home/user/data/img2.png']
            title:
                The title of the image group. If unspecified this will be randomly generated for you. This title should
                NOT include an extension. For example "encord_image_group".
            client_metadata:
                Optional arbitrary metadata to be associated with the image group. Should be a dictionary
                that is JSON-serializable.
            cloud_upload_settings:
                Settings for uploading data into the cloud. Change this object to overwrite the default values.

        Returns:
            UUID of the newly created image group item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the images could not be uploaded, e.g. due to being in an unsupported format.
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
        """
        Create an image group in Encord storage. Choose this type of image upload for sequential images (a timelapse
        or similar). A compressed video will be created from the images.

        See also :meth:`.Folder.create_image_group` and :meth:`.Folder.upload_image`.

        Args:
            file_paths: a list of paths to images, e.g.
                ['/home/user/data/img1.png', '/home/user/data/img2.png']
            title:
                The title of the image sequence. If unspecified this will be randomly generated for you. This title s
                should NOT include an extension. For example "front camera 2024-04-01".
            client_metadata:
                Optional arbitrary metadata to be associated with the image sequence. Should be a dictionary
                that is JSON-serializable.
            cloud_upload_settings:
                Settings for uploading data into the cloud. Change this object to overwrite the default values.

        Returns:
            UUID of the newly created image sequence item.

        Raises:
            AuthorizationError: If the user is not authorized to access the folder.
            EncordException: If the images could not be uploaded, e.g. due to being in an unsupported format.
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
    ):
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
            raise EncordException(f"Could not register image group, errors occured {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def add_private_data_to_folder_start(
        self,
        integration_id: str,
        private_files: Union[str, Dict, Path, TextIO],
        ignore_errors: bool = False,
    ) -> UUID:
        return self._add_data_to_folder_start(integration_id, private_files, ignore_errors)

    def add_private_data_to_folder_get_result(
        self,
        upload_job_id: UUID,
        timeout_seconds: int = 7 * 24 * 60 * 60,  # 7 days
    ) -> orm_storage.UploadLongPollingState:
        return self._add_data_to_folder_get_result(upload_job_id, timeout_seconds)

    def list_subfolders(
        self,
        *,
        search: Optional[str] = None,
        dataset_synced: Optional[bool] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable["StorageFolder"]:
        """
        List subfolders of the current folder.

        Args:
            search: Search string to filter folders by name (optional)
            dataset_synced: Include or exclude folders that are mirrored by a dataset. Optional; if `None`,
                no filtering is applied.
            order: Sort order for the folders. See :class:`encord.storage.FoldersSortBy` for available options.
            desc: If True, sort in descending order.
            page_size: Number of folders to return per page.

        Returns:
            Iterable of :class:`encord.StorageFolder` objects.
        """

        return StorageFolder._list_folders(
            self._api_client,
            f"storage/folders/{self.uuid}/folders",
            orm_storage.ListFoldersParams(
                search=search,
                dataset_synced=dataset_synced,
                order=order,
                desc=desc,
                page_size=page_size,
            ),
        )

    def find_subfolders(
        self,
        search: Optional[str] = None,
        dataset_synced: Optional[bool] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable["StorageFolder"]:
        """
        Recursively search for storage folders, starting from this folder.

        Args:
            search: Search string to filter folders by name (optional)
            dataset_synced: Include or exclude folders that are mirrored by a dataset. Optional; if `None`,
                no filtering is applied.
            order: Sort order for the folders. See :class:`encord.storage.FoldersSortBy` for available options.
            desc: If True, sort in descending order.
            page_size: Number of folders to return per page.

        Returns:
            Iterable of :class:`encord.StorageFolder` objects.
        """

        return StorageFolder._list_folders(
            self._api_client,
            f"storage/folders/{self.uuid}/folders",
            orm_storage.ListFoldersParams(
                search=search,
                is_recursive=True,
                dataset_synced=dataset_synced,
                order=order,
                desc=desc,
                page_size=page_size,
            ),
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
    ):
        """
        Recursively search for storage items, starting from this folder.

        Args:
            search: Search string to filter items by name.
            is_in_dataset: Filter items by whether they are linked to any dataset. `True` and `False` select
                only linked and only unlinked items, respectively. `None` includes all items regardless of their
                dataset links.
            item_types: Filter items by type.
            order: Sort order.
            desc: Sort in descending order.
            get_signed_urls: If True, return signed URLs for the items.
            page_size: Number of items to return per page.

        At least one of `search` or `item_types` must be provided.

        Returns:
            Iterable of items in the folder and its subfolders.
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
        """
        Get a summary of the folder (total size, number of items, etc). See :class:`encord.StorageFolderSummary` for
        exact set of information provided.
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
        """
        Update the folder's modifiable properties. Any parameters that are not provided will not be updated.

        Args:
            name: New folder name.
            description: New folder description.
            client_metadata: New client metadata.
            bundle: Optional :class:`encord.http.Bundle` to use for the operation. If provided, the operation
                will be bundled into a single server call with other item updates using the same bundle.

        Returns:
            None
        """
        if name is None and description is None and client_metadata is None:
            return

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
        """
        Move the folder to another folder (specify folder object or UUID),
        or to the root level if `target_folder` is None.
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

    def move_items_to_folder(
        self,
        target_folder: Union["StorageFolder", UUID],
        items_to_move: Sequence[Union[UUID, "StorageItem"]],
        allow_mirror_dataset_changes: bool = False,
    ) -> None:
        """
        Move items (list of `StorageItem` objects or UUIDs) to another folder (specify folder object or UUID).

        Args:
            target_folder: Target folder to move items to.
            items_to_move: List of items to move. All the items should be immediate children
                of the current folder.
            allow_mirror_dataset_changes: If `True`, allow moving items that are linked to a mirror dataset. By default,
                moving such items is prohibited, as it would result in data units being removed from a dataset,
                potentially deleting related annotations and other data.

        Returns:
            `None`
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

    def delete_storage_items(self, item_uuids: List[UUID], remove_unused_frames=True) -> None:
        """
        Delete storage items by their UUIDs.

        Args:
            item_uuids: List of UUIDs of items to delete. All the items should be immediate children
                of the current folder.
            remove_unused_frames: If `True` (which is default), then for every image group or DICOM series item,
            find and remove the individual images or DICOM files that are not used in any other item.

        Returns:
            `None`
        """
        self._api_client.post(
            f"/storage/folders/{self.uuid}/items/delete",
            params=None,
            payload=orm_storage.DeleteItemsPayload(child_uuids=item_uuids, remove_unused_frames=remove_unused_frames),
            result_type=None,  # we don't need a result here, even though the server provides it
        )

    def refetch_data(self) -> None:
        """
        Refetch data for the folder.
        """
        self._set_orm_folder(
            self._api_client.get(f"storage/folders/{self.uuid}", params=None, result_type=orm_storage.StorageFolder)
        )

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

    def _guess_title(self, title: Optional[str], file_path: Union[Path, str]) -> str:
        if title:
            return title

        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.name

    def _get_content_type(self, file_path: Union[Path, str], item_type: StorageItemType) -> str:
        if item_type == StorageItemType.IMAGE:
            return mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        elif item_type == StorageItemType.VIDEO:
            return "application/octet-stream"
        elif item_type == StorageItemType.DICOM_FILE:
            return "application/dicom"
        else:
            raise ValueError(f"Unsupported upload item type `{item_type}`")

    def _upload_local_file(
        self,
        file_path: Union[Path, str],
        title: str,
        item_type: StorageItemType,
        signed_url: str,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> None:
        content_type = self._get_content_type(file_path, item_type)

        if cloud_upload_settings.max_retries is not None:
            max_retries = cloud_upload_settings.max_retries
        else:
            max_retries = DEFAULT_REQUESTS_SETTINGS.max_retries

        if cloud_upload_settings.backoff_factor is not None:
            backoff_factor = cloud_upload_settings.backoff_factor
        else:
            backoff_factor = DEFAULT_REQUESTS_SETTINGS.backoff_factor

        _upload_single_file(
            str(file_path),
            {
                "signed_url": signed_url,
                "title": title,
            },
            content_type,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
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
            raise encord.exceptions.EncordException(f"folder.add_data errors occured {res.errors}")
        else:
            raise ValueError(f"res.status={res.status}, this should never happen")

    def _add_data_to_folder_start(
        self,
        integration_id: Optional[str],
        private_files: Union[str, Dict, Path, TextIO, DataUploadItems],
        ignore_errors: bool = False,
    ) -> UUID:
        if isinstance(private_files, dict):
            files: Optional[dict] = private_files
        elif isinstance(private_files, str):
            if os.path.exists(private_files):
                text_contents = Path(private_files).read_text(encoding="utf-8")
            else:
                text_contents = private_files

            files = json.loads(text_contents)
        elif isinstance(private_files, Path):
            text_contents = private_files.read_text(encoding="utf-8")
            files = json.loads(text_contents)
        elif isinstance(private_files, TextIO):
            text_contents = private_files.read()
            files = json.loads(text_contents)
        elif isinstance(private_files, DataUploadItems):
            files = None
        else:
            raise ValueError(f"Type [{type(private_files)}] of argument private_files is not supported")

        payload = orm_storage.PostUploadJobParams(
            data_items=private_files if isinstance(private_files, DataUploadItems) else None,
            external_files=files,
            integration_hash=UUID(integration_id) if integration_id is not None else None,
            ignore_errors=ignore_errors,
        )

        upload_job_id = self._api_client.post(
            path=f"storage/folders/{self.uuid}/data-upload-jobs",
            params=None,
            payload=payload,
            result_type=UUID,
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

                if polling_available_seconds == 0 or res.status in [LongPollingStatus.DONE, LongPollingStatus.ERROR]:
                    return res

                files_finished_count = res.units_done_count + res.units_error_count
                files_total_count = res.units_pending_count + res.units_done_count + res.units_error_count

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
        """ """
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
        """ """
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


class StorageItem:
    def __init__(self, api_client: ApiClient, orm_item: orm_storage.StorageItem):
        self._api_client = api_client
        self._orm_item = orm_item
        self._parsed_metadata: Optional[Dict[str, Any]] = None

    @property
    def uuid(self) -> UUID:
        return self._orm_item.uuid

    @property
    def parent_folder_uuid(self) -> UUID:
        return self._orm_item.parent

    def parent_folder(self) -> StorageFolder:
        return StorageFolder._get_folder(self._api_client, self.parent_folder_uuid)

    @property
    def item_type(self) -> StorageItemType:
        return self._orm_item.item_type

    @property
    def name(self) -> str:
        return self._orm_item.name

    @property
    def description(self) -> str:
        return self._orm_item.description

    @property
    def client_metadata(self) -> Optional[Dict[str, Any]]:
        if self._parsed_metadata is None:
            if self._orm_item.client_metadata is not None:
                self._parsed_metadata = json.loads(self._orm_item.client_metadata)
        return self._parsed_metadata

    @property
    def created_at(self) -> datetime:
        return self._orm_item.created_at

    @property
    def last_edited_at(self) -> datetime:
        return self._orm_item.last_edited_at

    @property
    def backed_data_units_count(self) -> int:
        return self._orm_item.backed_data_units_count

    @property
    def storage_location(self) -> orm_storage.StorageLocationName:
        return self._orm_item.storage_location

    @property
    def integration_hash(self) -> Optional[UUID]:
        return self._orm_item.integration_hash

    @property
    def url(self) -> Optional[str]:
        return self._orm_item.url

    @property
    def file_size(self) -> Optional[int]:
        return self._orm_item.file_size

    @property
    def mime_type(self) -> Optional[str]:
        return self._orm_item.mime_type

    @property
    def duration(self) -> Optional[float]:
        return self._orm_item.duration

    @property
    def fps(self) -> Optional[float]:
        return self._orm_item.fps

    @property
    def height(self) -> Optional[int]:
        return self._orm_item.height

    @property
    def width(self) -> Optional[int]:
        return self._orm_item.width

    @property
    def dicom_instance_uid(self) -> Optional[str]:
        return self._orm_item.dicom_instance_uid

    @property
    def dicom_study_uid(self) -> Optional[str]:
        return self._orm_item.dicom_study_uid

    @property
    def dicom_series_uid(self) -> Optional[str]:
        return self._orm_item.dicom_series_uid

    @property
    def frame_count(self) -> Optional[int]:
        return self._orm_item.frame_count

    def get_signed_url(self, refetch: bool = False) -> Optional[str]:
        """
        Get a signed URL for the item. This URL can be used to download the item.

        Will return `None` if the item is "synthetic" entity: an image group or a DICOM series. Note
        that image sequences are backed by a video file and will have a signed URL.
        """
        if self.item_type == StorageItemType.DICOM_SERIES or self.item_type == StorageItemType.IMAGE_GROUP:
            return None  # not supported for these types. Maybe raise ValueError instead?

        if refetch or self._orm_item.signed_url is None:
            self.refetch_data(get_signed_url=True)

        return self._orm_item.signed_url

    def get_summary(self) -> StorageItemSummary:
        """
        Get a summary of the item (linked datasets, etc.). See :class:`encord.StorageItemSummary` for
        exact set of information provided.
        """
        return self._api_client.get(
            f"storage/folders/{self.parent_folder_uuid}/items/{self.uuid}/summary",
            params=None,
            result_type=StorageItemSummary,
        )

    def get_child_items(self, get_signed_urls: bool = False) -> Iterable["StorageItem"]:
        """
        Get child items of the item (e.g. frames of an image group or files of DICOM series).
        Only returns those items that are accessible to the user. See also :meth:`.get_summary`.

        Args:
            get_signed_urls: If True, get signed URLs for the child items.

        Returns:
            List of child items. The list will be emtpy if the item has no children (e.g. it's a Video)
        """
        if self.item_type not in {
            StorageItemType.IMAGE_GROUP,
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
        bundle: Optional[Bundle] = None,
    ) -> None:
        """
        Update the item's modifiable properties. Any parameters that are not provided will not be updated.

        Args:
            name: New item name.
            description: New item description.
            client_metadata: New client metadata.
            bundle: Optional :class:`encord.http.Bundle` to use for the operation. If provided, the operation
                will be bundled into a single server call with other item updates using the same bundle.

        Returns:
            None
        """
        if name is None and description is None and client_metadata is None:
            return

        if bundle is not None:
            bundled_operation(
                bundle,
                operation=self._api_client.get_bound_operation(StorageItem._patch_multiple_items),
                payload=orm_storage.BundledPatchItemPayload(
                    item_patches={
                        str(self.uuid): PatchItemPayload(
                            name=name,
                            description=description,
                            client_metadata=client_metadata,
                        ),
                    },
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
                payload=PatchItemPayload(
                    name=name,
                    description=description,
                    client_metadata=client_metadata,
                ),
                result_type=orm_storage.StorageItem,
            )

    def delete(self, remove_unused_frames=True) -> None:
        """
        Delete the item from the storage.

        Args:
            remove_unused_frames: If `True` (which is default) and the item is an image group or a DICOM series,
            find and remove the individual images or DICOM files that are not used in any other item.

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
    ):
        """
        Move the item to another folder (specify folder object or UUID).

        Args:
            target_folder: Target folder to move the item to. Should be a `StorageFolder` object or a UUID.

            allow_mirror_dataset_changes: If `True`, allow moving items that are linked to a mirror dataset. By default,
                moving such items is prohibited, as it would result in data units being removed from a dataset,
                potentially deleting related annotations and other data.

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
        """
        Refetch data for the item.
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
            result_type=Page[orm_storage.StorageItem],  # it's always just one page here
        )
        return [StorageItem(api_client, orm_item) for orm_item in orm_items.results]

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
