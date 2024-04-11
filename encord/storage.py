import json
import mimetypes
import os
import time
from math import ceil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, TextIO, Union
from uuid import UUID

import requests

import encord
import encord.orm.storage as orm_storage
from encord.client import LONG_POLLING_RESPONSE_RETRY_N, LONG_POLLING_SLEEP_ON_FAILURE_SECONDS
from encord.exceptions import EncordException
from encord.http.constants import DEFAULT_REQUESTS_SETTINGS
from encord.http.utils import CloudUploadSettings, _upload_single_file
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.dataset import LongPollingStatus
from encord.orm.storage import (
    CustomerProvidedVideoMetadata,
    DataUploadItems,
    FoldersSortBy,
    StorageItemType,
    UploadSignedUrlsPayload,
)


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

    def delete(self):
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
                        ].object_key,  #  this is actually ignored when placeholder_item_uuid is set
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
                        ].object_key,  #  this is actually ignored when placeholder_item_uuid is set
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
            raise EncordException(f"Could not register image, errors occured {upload_result.errors}")
        else:
            return upload_result.items_with_names[0].item_uuid

    def create_dicom_series(
        self,
        file_paths: List[str],
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
        file_paths: List[str],
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
        file_paths: List[str],
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
        file_paths: List[str],
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
            self.uuid,
            global_search=False,
            search=search,
            dataset_synced=dataset_synced,
            order=order,
            desc=desc,
            page_size=page_size,
        )

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

        print(f"add_data_to_folder job started with upload_job_id={upload_job_id}.")
        print("SDK process can be terminated, this will not affect successful job execution.")
        print("You can follow the progress in the web app via notifications.")

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
                    print(f"add_private_data_to_dataset job completed with upload_job_id={upload_job_id}.")

                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                if polling_available_seconds == 0 or res.status in [LongPollingStatus.DONE, LongPollingStatus.ERROR]:
                    return res

                files_finished_count = res.units_done_count + res.units_error_count
                files_total_count = res.units_pending_count + res.units_done_count + res.units_error_count

                if files_finished_count != files_total_count:
                    print(f"Processed {files_finished_count}/{files_total_count} files")
                else:
                    print("Processed all files, dataset data linking and task creation is performed, please wait")

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
        parent_uuid: Optional[UUID],
        global_search: bool,
        search: Optional[str] = None,
        dataset_synced: Optional[bool] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable["StorageFolder"]:
        """ """

        if page_size < 1 or page_size > 1000:
            raise ValueError("page_size should be between 1 and 1000")

        params = orm_storage.ListFoldersParams(
            search=search,
            dataset_synced=dataset_synced,
            order=order,
            desc=desc,
            page_token=None,
            page_size=page_size,
        )

        path: str
        if parent_uuid is not None:
            path = f"storage/folders/{parent_uuid}/folders"
        elif global_search:
            path = "storage/search/folders"
        else:
            path = "storage/folders"

        while True:
            page = api_client.get(path, params=params, result_type=Page[orm_storage.StorageFolder])

            for orm_folder in page.results:
                yield StorageFolder(api_client, orm_folder)

            if page.next_page_token is not None:
                params.page_token = page.next_page_token
            else:
                break

    @staticmethod
    def _search_folders(
        api_client: ApiClient,
        search: Optional[str] = None,
        dataset_synced: Optional[bool] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable["StorageFolder"]:
        """ """

        if page_size < 1 or page_size > 1000:
            raise ValueError("page_size should be between 1 and 1000")

        params = orm_storage.ListFoldersParams(
            search=search,
            dataset_synced=dataset_synced,
            order=order,
            desc=desc,
            page_token=None,
            page_size=page_size,
        )

        while True:
            page = api_client.get("storage/folders", params=params, result_type=Page[orm_storage.StorageFolder])

            for orm_folder in page.results:
                yield StorageFolder(api_client, orm_folder)

            if page.next_page_token is not None:
                params.page_token = page.next_page_token
            else:
                break
