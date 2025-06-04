"""``encord.client`` provides a simple Python client that allows you
to query project resources through the Encord API.

Here is a simple example for instantiating the client for a project
and obtaining project info:

.. test_blurb2.py code::

    from encord.client import EncordClient

    client = EncordClient.initialize('YourProjectID', 'YourAPIKey')
    client.get_project()

Returns:
        Project: A project record instance. See Project ORM for details.

"""

from __future__ import annotations

import dataclasses
import json
import logging
import os.path
import time
import typing
import uuid
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union, cast
from uuid import UUID

import requests

import encord.exceptions
from encord.common.deprecated import deprecated
from encord.configs import Config
from encord.constants.enums import DataType
from encord.constants.string_constants import (
    INTERPOLATION,
)
from encord.http.querier import Querier
from encord.http.utils import (
    CloudUploadSettings,
    upload_to_signed_url_list,
)
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.active import ActiveProjectImportPayload, ActiveProjectMode
from encord.orm.analytics import CollaboratorTimer, CollaboratorTimerParams, TimeSpent, TimeSpentParams
from encord.orm.bearer_request import BearerTokenResponse
from encord.orm.cloud_integration import CloudIntegration, GetCloudIntegrationsResponse
from encord.orm.dataset import (
    DEFAULT_DATASET_ACCESS_SETTINGS,
    AddPrivateDataResponse,
    DataLinkDuplicatesBehavior,
    DataRow,
    DataRows,
    DatasetAccessSettings,
    DatasetData,
    DatasetDataLongPolling,
    DatasetLinkItems,
    DatasetUser,
    DatasetUserRole,
    DatasetUsers,
    DicomSeries,
    Image,
    ImageGroup,
    ImageGroupOCR,
    Images,
    LongPollingStatus,
    ReEncodeVideoTask,
    Video,
)
from encord.orm.dataset import Dataset as OrmDataset
from encord.orm.group import (
    AddDatasetGroupsPayload,
    AddProjectGroupsPayload,
    DatasetGroup,
    ProjectGroup,
    RemoveGroupsParams,
)
from encord.orm.label_log import LabelLog, LabelLogParams
from encord.orm.label_row import (
    AnnotationTaskStatus,
    LabelRow,
    LabelRowMetadata,
    LabelValidationState,
    ShadowDataState,
)
from encord.orm.labeling_algorithm import (
    BoundingBoxFittingParams,
    LabelingAlgorithm,
    ObjectInterpolationParams,
)
from encord.orm.project import (
    CopyDatasetAction,
    CopyDatasetOptions,
    CopyLabelsOptions,
    CopyProjectPayload,
    ProjectCopy,
    ProjectCopyOptions,
    ProjectDataset,
    ProjectStatus,
    ProjectUsers,
    SetProjectStatusPayload,
    TaskPriorityParams,
)
from encord.orm.project import Project as OrmProject
from encord.orm.project import ProjectDTO as ProjectOrmV2
from encord.orm.storage import (
    DatasetDataLongPollingParams,
    DataUploadDicomSeries,
    DataUploadDicomSeriesDicomFile,
    DataUploadImage,
    DataUploadImageGroup,
    DataUploadImageGroupImage,
    DataUploadItems,
    DataUploadVideo,
    StorageItemType,
)
from encord.orm.workflow import (
    LabelWorkflowGraphNode,
    LabelWorkflowGraphNodePayload,
    WorkflowAction,
)
from encord.project_ontology.classification_type import ClassificationType
from encord.project_ontology.object_type import ObjectShape
from encord.project_ontology.ontology import Ontology as LegacyOntology
from encord.utilities.client_utilities import optional_datetime_to_iso_str, optional_set_to_list
from encord.utilities.project_user import ProjectUser, ProjectUserRole

LONG_POLLING_RESPONSE_RETRY_N = 3
LONG_POLLING_SLEEP_ON_FAILURE_SECONDS = 10
LONG_POLLING_MAX_REQUEST_TIME_SECONDS = 60
LONG_POLLING_MAX_REQUEST_SINGLE_ITEM_TIME_SECONDS = 10

logger = logging.getLogger(__name__)


class EncordClient:
    """Encord client. Allows you to query db items associated
    with a project (e.g. label rows, datasets).
    """

    def __init__(self, querier: Querier, config: Config, api_client: ApiClient):
        self._querier = querier
        self._config = config
        self._api_client = api_client

    @deprecated(version="0.1.154", alternative="EncordUserClient.get_cloud_integrations")
    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return [
            CloudIntegration(
                id=str(x.integration_uuid),
                title=x.title,
            )
            for x in self._api_client.get(
                "cloud-integrations",
                params=None,
                result_type=GetCloudIntegrationsResponse,
            ).result
        ]

    def get_bearer_token(self) -> BearerTokenResponse:
        return self._api_client.get("user/bearer-token", None, result_type=BearerTokenResponse)


class EncordClientDataset(EncordClient):
    """DEPRECATED - prefer using the :class:`encord.dataset.Dataset` instead"""

    def __init__(
        self,
        querier: Querier,
        config: Config,
        dataset_access_settings: DatasetAccessSettings = DEFAULT_DATASET_ACCESS_SETTINGS,
        api_client: Optional[ApiClient] = None,
    ):
        if api_client is None:
            raise ValueError("api_client is None")

        super().__init__(querier, config, api_client)
        self._dataset_access_settings = dataset_access_settings

    def get_dataset(self) -> OrmDataset:
        """Retrieve dataset info (pointers to data, labels).

        Returns:
            OrmDataset: A dataset record instance.

        Raises:
            AuthorisationError: If the dataset API key is invalid.
            ResourceNotFoundError: If no dataset exists by the specified dataset EntityId.
            UnknownError: If an error occurs while retrieving the dataset.
        """
        res = self._querier.basic_getter(
            OrmDataset,
            payload={
                "dataset_access_settings": dataclasses.asdict(self._dataset_access_settings),
            },
        )

        for row in res.data_rows:
            row["_querier"] = self._querier
        return res

    def list_data_rows(
        self,
        title_eq: Optional[str] = None,
        title_like: Optional[str] = None,
        created_before: Optional[Union[str, datetime]] = None,
        created_after: Optional[Union[str, datetime]] = None,
        data_types: Optional[List[DataType]] = None,
        data_hashes: Optional[List[str]] = None,
    ) -> List[DataRow]:
        """Retrieve dataset rows (pointers to data, labels).

        Args:
            title_eq: optional exact title row filter
            title_like: optional fuzzy title row filter; SQL syntax
            created_before: optional datetime row filter
            created_after: optional datetime row filter
            data_types: optional data types row filter
            data_hashes: optional list of individual data unit hashes to include

        Returns:
            List[DataRow]: A list of DataRows object that match the filter

        Raises:
            AuthorisationError: If the dataset API key is invalid.
            ResourceNotFoundError: If no dataset exists by the specified dataset EntityId.
            UnknownError: If an error occurs while retrieving the dataset.
        """
        created_before = optional_datetime_to_iso_str("created_before", created_before)
        created_after = optional_datetime_to_iso_str("created_after", created_after)

        data_rows = cast(
            List[DataRow],
            self._querier.get_multiple(
                DataRows,
                payload={
                    "title_eq": title_eq,
                    "title_like": title_like,
                    "created_before": created_before,
                    "created_after": created_after,
                    "data_types": [data_type.to_upper_case_string() for data_type in data_types]
                    if data_types is not None
                    else None,
                    "dataset_access_settings": dataclasses.asdict(self._dataset_access_settings),
                    "data_hashes": data_hashes,
                },
            ),
        )

        for row in data_rows:
            row["_querier"] = self._querier

        return data_rows

    def set_access_settings(self, dataset_access_settings: DatasetAccessSettings) -> None:
        self._dataset_access_settings = dataset_access_settings

    def add_users(self, user_emails: List[str], user_role: DatasetUserRole) -> List[DatasetUser]:
        """This function is documented in :meth:`encord.project.Dataset.add_users`."""
        payload = {"user_emails": user_emails, "user_role": user_role}
        users = self._querier.basic_setter(DatasetUsers, self._querier.resource_id, payload=payload)

        return [DatasetUser.from_dict(user) for user in users]

    def list_groups(self, dataset_hash: uuid.UUID) -> Page[DatasetGroup]:
        return self._api_client.get(f"datasets/{dataset_hash}/groups", params=None, result_type=Page[DatasetGroup])

    def add_groups(self, dataset_hash: str, group_hash: List[uuid.UUID], user_role: DatasetUserRole) -> None:
        payload = AddDatasetGroupsPayload(group_hash_list=group_hash, user_role=user_role)
        self._api_client.post(f"datasets/{dataset_hash}/groups", params=None, payload=payload, result_type=None)

    def remove_groups(self, dataset_hash: uuid.UUID, group_hash: List[uuid.UUID]) -> None:
        params = RemoveGroupsParams(group_hash_list=group_hash)
        self._api_client.delete(f"datasets/{dataset_hash}/groups", params=params, result_type=None)

    def __add_data_to_dataset_get_result(
        self,
        upload_job_id: str,
        timeout_seconds: int = 7 * 24 * 60 * 60,  # 7 days
    ) -> DatasetDataLongPolling:
        failed_requests_count = 0
        polling_start_timestamp = time.perf_counter()

        while True:
            try:
                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                res = self._querier.basic_getter(
                    DatasetDataLongPolling,
                    self._querier.resource_id,
                    payload={
                        "process_hash": upload_job_id,
                        "timeout_seconds": min(
                            polling_available_seconds,
                            LONG_POLLING_MAX_REQUEST_SINGLE_ITEM_TIME_SECONDS,
                        ),
                    },
                )

                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                if polling_available_seconds == 0 or res.status in [
                    LongPollingStatus.DONE,
                    LongPollingStatus.ERROR,
                    LongPollingStatus.CANCELLED,
                ]:
                    return res

                failed_requests_count = 0
            except (requests.exceptions.RequestException, encord.exceptions.RequestException):
                failed_requests_count += 1

                if failed_requests_count >= LONG_POLLING_RESPONSE_RETRY_N:
                    raise

                time.sleep(LONG_POLLING_SLEEP_ON_FAILURE_SECONDS)

    def upload_video(
        self,
        file_path: Union[str, Path],
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        title: Optional[str] = None,
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> Video:
        """This function is documented in :meth:`encord.dataset.Dataset.upload_video`."""
        signed_url = upload_to_signed_url_list(
            file_paths=[file_path],
            config=self._config,
            api_client=self._api_client,
            upload_item_type=StorageItemType.VIDEO,
            cloud_upload_settings=cloud_upload_settings,
        )[0]

        upload_job_id = self._querier.basic_setter(
            DatasetDataLongPolling,
            uid=self._querier.resource_id,
            payload=DatasetDataLongPollingParams(
                data_items=DataUploadItems(
                    videos=[
                        DataUploadVideo(
                            object_url=signed_url["file_link"],
                            title=title or signed_url["title"],
                        )
                    ],
                ),
                files=None,
                integration_id=None,
                ignore_errors=False,
                folder_uuid=folder_uuid,
                file_name=None,
            ),
        )["process_hash"]

        res = self.__add_data_to_dataset_get_result(upload_job_id)

        if res.status == LongPollingStatus.DONE:
            if len(res.data_hashes_with_titles) != 1:
                raise encord.exceptions.EncordException(
                    f"An error has occurred during video upload. len({res.data_hashes_with_titles=}) != 1, {upload_job_id=}"
                )

            res_item = res.data_hashes_with_titles[0]
            logger.info(f"Upload complete. {upload_job_id=}")

            return Video(  # Video model types annotations are not correct
                {
                    "data_hash": res_item.data_hash,
                    "title": res_item.title,
                }
            )
        elif res.status == LongPollingStatus.ERROR:
            raise encord.exceptions.EncordException(
                f"An error has occurred during video upload. {res.errors=}, {upload_job_id=}"
            )
        else:
            raise ValueError(f"{res.status=}, this should never happen, {upload_job_id=}")

    def create_image_group(
        self,
        file_paths: Iterable[Union[str, Path]],
        max_workers: Optional[int] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        title: Optional[str] = None,
        *,
        create_video: bool = True,
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> List[ImageGroup]:
        """This function is documented in :meth:`encord.dataset.Dataset.create_image_group`."""
        signed_urls = upload_to_signed_url_list(
            file_paths=file_paths,
            config=self._config,
            api_client=self._api_client,
            upload_item_type=StorageItemType.IMAGE,
            cloud_upload_settings=cloud_upload_settings,
        )

        if not signed_urls:
            raise encord.exceptions.EncordException("All image uploads failed. Image group was not created.")

        upload_job_id = self._querier.basic_setter(
            DatasetDataLongPolling,
            uid=self._querier.resource_id,
            payload=DatasetDataLongPollingParams(
                data_items=DataUploadItems(
                    image_groups=[
                        DataUploadImageGroup(
                            images=[
                                DataUploadImageGroupImage(
                                    url=x["file_link"],
                                    title=x["title"],
                                )
                                for x in signed_urls
                            ],
                            title=title,
                            create_video=create_video,
                            cluster_by_resolution=create_video,  # cluster_by_resolution only if videos are created
                        )
                    ],
                ),
                files=None,
                integration_id=None,
                ignore_errors=False,
                folder_uuid=folder_uuid,
                file_name=None,
            ),
        )["process_hash"]

        res = self.__add_data_to_dataset_get_result(upload_job_id)

        if res.status == LongPollingStatus.DONE:
            if not res.data_hashes_with_titles:
                raise encord.exceptions.EncordException(
                    f"An error has occurred during image group creation. {res.data_hashes_with_titles=} is empty, {upload_job_id=}"
                )

            titles = [x.title for x in res.data_hashes_with_titles]
            logger.info(f"Upload successful! {titles} created, {upload_job_id=}")

            return [
                ImageGroup(
                    {
                        "data_hash": x.data_hash,
                        "title": x.title,
                    }
                )
                for x in res.data_hashes_with_titles
            ]
        elif res.status == LongPollingStatus.ERROR:
            raise encord.exceptions.EncordException(
                f"An error has occurred during image group creation. {res.errors=}, {upload_job_id=}"
            )
        else:
            raise ValueError(f"{res.status=}, this should never happen, {upload_job_id=}")

    def create_dicom_series(
        self,
        file_paths: Union[typing.Collection[str], typing.Collection[Path], typing.Collection[Union[str, Path]]],
        title: Optional[str] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> Dict:
        """This function is documented in :meth:`encord.dataset.Dataset.create_dicom_series`."""
        signed_urls = upload_to_signed_url_list(
            file_paths=file_paths,
            config=self._config,
            api_client=self._api_client,
            upload_item_type=StorageItemType.DICOM_FILE,
            cloud_upload_settings=cloud_upload_settings,
        )

        if not signed_urls:
            raise encord.exceptions.EncordException("DICOM files upload failed. The DICOM series was not created.")

        upload_job_id = self._querier.basic_setter(
            DatasetDataLongPolling,
            uid=self._querier.resource_id,
            payload=DatasetDataLongPollingParams(
                data_items=DataUploadItems(
                    dicom_series=[
                        DataUploadDicomSeries(
                            dicom_files=[
                                DataUploadDicomSeriesDicomFile(
                                    url=x["file_link"],
                                    title=x["title"],
                                )
                                for x in signed_urls
                            ],
                            title=title,
                        )
                    ],
                ),
                files=None,
                integration_id=None,
                ignore_errors=False,
                folder_uuid=folder_uuid,
                file_name=None,
            ),
        )["process_hash"]

        res = self.__add_data_to_dataset_get_result(upload_job_id)

        if res.status == LongPollingStatus.DONE:
            if len(res.data_hashes_with_titles) != 1:
                raise encord.exceptions.EncordException(
                    f"An error has occurred during the DICOM series creation. len({res.data_hashes_with_titles=}) != 1, {upload_job_id=}"
                )

            res_item = res.data_hashes_with_titles[0]

            return {
                "data_hash": res_item.data_hash,
                "title": res_item.title,
            }
        elif res.status == LongPollingStatus.ERROR:
            raise encord.exceptions.EncordException(
                f"An error has occurred during the DICOM series creation. {res.errors=}, {upload_job_id=}"
            )
        else:
            raise ValueError(f"{res.status=}, this should never happen, {upload_job_id=}")

    def upload_image(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> Image:
        """This function is documented in :meth:`encord.dataset.Dataset.upload_image`."""
        signed_urls = upload_to_signed_url_list(
            file_paths=[file_path],
            config=self._config,
            api_client=self._api_client,
            upload_item_type=StorageItemType.IMAGE,
            cloud_upload_settings=cloud_upload_settings,
        )

        if not signed_urls:
            raise encord.exceptions.EncordException("Image upload failed.")

        signed_url = signed_urls[0]

        upload_job_id = self._querier.basic_setter(
            DatasetDataLongPolling,
            uid=self._querier.resource_id,
            payload=DatasetDataLongPollingParams(
                data_items=DataUploadItems(
                    images=[
                        DataUploadImage(
                            object_url=signed_url["file_link"],
                            title=title or signed_url["title"],
                        )
                    ],
                ),
                files=None,
                integration_id=None,
                ignore_errors=False,
                folder_uuid=folder_uuid,
                file_name=None,
            ),
        )["process_hash"]

        res = self.__add_data_to_dataset_get_result(upload_job_id)

        if res.status == LongPollingStatus.DONE:
            if len(res.data_hashes_with_titles) != 1:
                raise encord.exceptions.EncordException(
                    f"An error has occurred during the image upload. len({res.data_hashes_with_titles=}) != 1, {upload_job_id=}"
                )

            res_item = res.data_hashes_with_titles[0]

            return Image(
                {
                    "data_hash": res_item.data_hash,
                    "title": res_item.title,
                    "file_link": signed_url["file_link"],
                }
            )
        elif res.status == LongPollingStatus.ERROR:
            raise encord.exceptions.EncordException(
                f"An error has occurred during the image upload. {res.errors=}, {upload_job_id=}"
            )
        else:
            raise ValueError(f"{res.status=}, this should never happen, {upload_job_id=}")

    def link_items(
        self,
        item_uuids: List[uuid.UUID],
        duplicates_behavior: DataLinkDuplicatesBehavior = DataLinkDuplicatesBehavior.SKIP,
    ) -> List[DataRow]:
        """Link storage items to the dataset, creating new data rows.

        Args:
            item_uuids: List of item UUIDs to link to the dataset
            duplicates_behavior: The behavior to follow when encountering duplicates. Defaults to `SKIP`. See also
                :class:`encord.orm.dataset.DataLinkDuplicatesBehavior`
        """
        data_row_dicts = self._querier.basic_setter(
            DatasetLinkItems,
            uid=self._querier.resource_id,
            payload={
                "item_uuids": [str(item_uuid) for item_uuid in item_uuids],
                "duplicates_behavior": duplicates_behavior.value,
            },
        )
        return DataRow.from_dict_list(data_row_dicts)

    def delete_data(self, data_hashes: Union[List[str], str]):
        """This function is documented in :meth:`encord.dataset.Dataset.delete_data`."""
        if isinstance(data_hashes, str):
            data_hashes = [data_hashes]
        self._querier.basic_delete(Video, uid=data_hashes)

    def add_private_data_to_dataset(
        self,
        integration_id: str,
        private_files: Union[str, typing.Dict, Path, typing.TextIO],
        ignore_errors: bool = False,
    ) -> AddPrivateDataResponse:
        """This function is documented in :meth:`encord.dataset.Dataset.add_private_data_to_dataset`."""
        upload_job_id = self.add_private_data_to_dataset_start(
            integration_id,
            private_files,
            ignore_errors,
        )

        res = self.add_private_data_to_dataset_get_result(upload_job_id)

        if res.status == LongPollingStatus.DONE:
            return AddPrivateDataResponse(dataset_data_list=res.data_hashes_with_titles)
        elif res.status == LongPollingStatus.ERROR:
            raise encord.exceptions.EncordException(
                f"add_private_data_to_dataset errors occurred {res.errors=}, {upload_job_id=}"
            )
        else:
            raise ValueError(f"{res.status=}, this should never happen, {upload_job_id=}")

    def add_private_data_to_dataset_start(
        self,
        integration_id: str,
        private_files: Union[str, typing.Dict, Path, typing.TextIO],
        ignore_errors: bool = False,
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> str:
        """This function is documented in :meth:`encord.dataset.Dataset.add_private_data_to_dataset_start`."""
        if isinstance(private_files, dict):
            files = private_files
            file_name: Optional[str] = None
        elif isinstance(private_files, str) and os.path.exists(private_files):
            text_contents = Path(private_files).read_text(encoding="utf-8")
            files = json.loads(text_contents)
            file_name = Path(private_files).name
        elif isinstance(private_files, str) and (not os.path.exists(private_files)):
            text_contents = private_files
            files = json.loads(text_contents)
            file_name = None
        elif isinstance(private_files, Path):
            text_contents = private_files.read_text(encoding="utf-8")
            files = json.loads(text_contents)
            file_name = private_files.name
        elif isinstance(private_files, typing.TextIO):
            text_contents = private_files.read()
            files = json.loads(text_contents)
            file_name = None
        else:
            raise ValueError(f"Type [{type(private_files)}] of argument private_files is not supported")

        process_hash = self._querier.basic_setter(
            DatasetDataLongPolling,
            uid=self._querier.resource_id,
            payload=DatasetDataLongPollingParams(
                data_items=None,
                files=files,
                integration_id=UUID(integration_id),
                ignore_errors=ignore_errors,
                folder_uuid=folder_uuid,
                file_name=file_name,
            ),
        )["process_hash"]

        logger.info(f"add_private_data_to_dataset job started with upload_job_id={process_hash}.")
        logger.info("SDK process can be terminated, this will not affect successful job execution.")
        logger.info("You can follow the progress in the web app via notifications.")

        return process_hash

    def add_private_data_to_dataset_get_result(
        self,
        upload_job_id: str,
        timeout_seconds: int = 7 * 24 * 60 * 60,  # 7 days
    ) -> DatasetDataLongPolling:
        """This function is documented in :meth:`encord.dataset.Dataset.add_private_data_to_dataset_get_result`."""
        failed_requests_count = 0
        polling_start_timestamp = time.perf_counter()

        while True:
            try:
                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                res = self._querier.basic_getter(
                    DatasetDataLongPolling,
                    self._querier.resource_id,
                    payload={
                        "process_hash": upload_job_id,
                        "timeout_seconds": min(
                            polling_available_seconds,
                            LONG_POLLING_MAX_REQUEST_TIME_SECONDS,
                        ),
                    },
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

    def update_data_item(self, data_hash: str, new_title: str) -> bool:
        """This function is documented in :meth:`encord.dataset.Dataset.update_data_item`."""
        payload = [{"video_hash": data_hash, "title": new_title}]

        response = self._querier.basic_setter(Video, self.get_dataset().dataset_hash, payload=payload)
        try:
            return response.get("success", False)
        except AttributeError:
            return False

    def re_encode_data(self, data_hashes: List[str]):
        """This function is documented in :meth:`encord.dataset.Dataset.re_encode_data`."""
        payload = {"data_hash": data_hashes}
        return self._querier.basic_put(ReEncodeVideoTask, uid=None, payload=payload)

    def re_encode_data_status(self, job_id: int):
        """This function is documented in :meth:`encord.dataset.Dataset.re_encode_data_status`."""
        return self._querier.basic_getter(ReEncodeVideoTask, uid=job_id)

    def run_ocr(self, image_group_id: str) -> List[ImageGroupOCR]:
        """This function is documented in :meth:`encord.dataset.Dataset.run_ocr`."""
        payload = {"image_group_data_hash": image_group_id}
        return self._querier.get_multiple(ImageGroupOCR, payload=payload)


class EncordClientProject(EncordClient):
    """DEPRECATED - prefer using the :class:`encord.project.Project` instead"""

    @property
    def project_hash(self) -> str:
        assert self._querier.resource_id, "Resource id can't be empty for created project client"
        return self._querier.resource_id  # type: ignore[attr-defined]

    def get_project(self, include_labels_metadata=True) -> OrmProject:
        """Retrieve project info (pointers to data, labels).

        Args:
            include_labels_metadata: if false, label row metadata information will not be returned.

        Returns:
            OrmProject: A project record instance.

        Raises:
            AuthorisationError: If the project API key is invalid.
            ResourceNotFoundError: If no project exists by the specified project EntityId.
            UnknownError: If an error occurs while retrieving the project.
        """
        return self._querier.basic_getter(
            OrmProject, payload={"include_labels_metadata": include_labels_metadata}, retryable=True
        )

    def get_project_v2(self) -> ProjectOrmV2:
        """This is an internal method, do not use it directly.
        Use :meth:`UserClient.get_project` instead.
        """
        return self._api_client.get(f"/projects/{self.project_hash}", params=None, result_type=ProjectOrmV2)

    def list_label_rows(
        self,
        edited_before: Optional[Union[str, datetime]] = None,
        edited_after: Optional[Union[str, datetime]] = None,
        label_statuses: Optional[List[AnnotationTaskStatus]] = None,
        shadow_data_state: Optional[ShadowDataState] = None,
        *,
        include_uninitialised_labels: bool = False,
        include_workflow_graph_node: bool = True,
        include_client_metadata: bool = False,
        include_images_data: bool = False,
        label_hashes: Optional[Union[List[str], List[UUID]]] = None,
        data_hashes: Optional[Union[List[str], List[UUID]]] = None,
        data_title_eq: Optional[str] = None,
        data_title_like: Optional[str] = None,
        workflow_graph_node_title_eq: Optional[str] = None,
        workflow_graph_node_title_like: Optional[str] = None,
        include_all_label_branches: bool = False,
        branch_name: Optional[str] = None,
    ) -> List[LabelRowMetadata]:
        """This function is documented in :meth:`encord.project.Project.list_label_rows`."""
        data_hashes = [str(data_hash) for data_hash in data_hashes] if data_hashes is not None else None
        label_hashes = [str(label_hash) for label_hash in label_hashes] if label_hashes is not None else None

        label_statuses_values = (
            [label_status.value for label_status in label_statuses] if label_statuses is not None else None
        )
        edited_before = optional_datetime_to_iso_str("edited_before", edited_before)
        edited_after = optional_datetime_to_iso_str("edited_after", edited_after)

        payload = {
            "edited_before": edited_before,
            "edited_after": edited_after,
            "label_statuses": label_statuses_values,
            "shadow_data_state": shadow_data_state.value if shadow_data_state else None,
            "include_uninitialised_labels": include_uninitialised_labels,
            "data_hashes": data_hashes,
            "label_hashes": label_hashes,
            "data_title_eq": data_title_eq,
            "data_title_like": data_title_like,
            "workflow_graph_node_title_eq": workflow_graph_node_title_eq,
            "workflow_graph_node_title_like": workflow_graph_node_title_like,
            "include_client_metadata": include_client_metadata,
            "include_images_data": include_images_data,
            "include_workflow_graph_node": include_workflow_graph_node,
            "include_all_label_branches": include_all_label_branches,
            "branch_name": branch_name,
        }
        return self._querier.get_multiple(LabelRowMetadata, payload=payload, retryable=True)

    def add_users(self, user_emails: List[str], user_role: ProjectUserRole) -> List[ProjectUser]:
        """This function is documented in :meth:`encord.project.Project.add_users`."""
        payload = {"user_emails": user_emails, "user_role": user_role}
        users = self._querier.basic_setter(ProjectUsers, self._querier.resource_id, payload=payload)

        return [ProjectUser.from_dict(user) for user in users]

    def list_groups(self, project_hash: uuid.UUID) -> Page[ProjectGroup]:
        return self._api_client.get(f"projects/{project_hash}/groups", params=None, result_type=Page[ProjectGroup])

    def add_groups(self, project_hash: uuid.UUID, group_hash: List[uuid.UUID], user_role: ProjectUserRole) -> None:
        payload = AddProjectGroupsPayload(group_hash_list=group_hash, user_role=user_role)
        self._api_client.post(f"projects/{project_hash}/groups", params=None, payload=payload, result_type=None)

    def remove_groups(self, group_hash: List[uuid.UUID]) -> None:
        params = RemoveGroupsParams(group_hash_list=group_hash)
        self._api_client.delete(f"projects/{self.project_hash}/groups", params=params, result_type=None)

    def copy_project(
        self,
        copy_datasets: Union[bool, CopyDatasetOptions] = False,
        copy_collaborators=False,
        copy_models=False,
        *,
        copy_labels: Optional[CopyLabelsOptions] = None,
        new_title: Optional[str] = None,
        new_description: Optional[str] = None,
    ) -> str:
        """This function is documented in :meth:`encord.project.Project.copy_project`."""
        payload = CopyProjectPayload()
        payload.project_copy_metadata = CopyProjectPayload._ProjectCopyMetadata(new_title)
        payload.copy_labels_options = CopyProjectPayload._CopyLabelsOptions()

        if payload.project_copy_metadata and new_description:
            payload.project_copy_metadata.project_description = new_description

        if copy_labels:
            payload.copy_project_options.append(ProjectCopyOptions.LABELS)
            if isinstance(copy_labels, CopyLabelsOptions):
                payload.copy_labels_options.accepted_label_hashes = copy_labels.accepted_label_hashes
                payload.copy_labels_options.accepted_label_statuses = copy_labels.accepted_label_statuses

        if copy_datasets:
            if copy_datasets is True or copy_datasets.action == CopyDatasetAction.ATTACH:
                payload.copy_project_options.append(ProjectCopyOptions.DATASETS)
            elif copy_datasets.action == CopyDatasetAction.CLONE:
                payload.project_copy_metadata.dataset_title = copy_datasets.dataset_title
                payload.project_copy_metadata.dataset_description = copy_datasets.dataset_description
                payload.copy_labels_options.create_new_dataset = True
                payload.copy_labels_options.datasets_to_data_hashes_map = copy_datasets.datasets_to_data_hashes_map

        if copy_models:
            payload.copy_project_options.append(ProjectCopyOptions.MODELS)
        if copy_collaborators:
            payload.copy_project_options.append(ProjectCopyOptions.COLLABORATORS)

        return self._querier.basic_setter(ProjectCopy, self._querier.resource_id, payload=dataclasses.asdict(payload))

    def get_label_row(
        self,
        uid: str,
        get_signed_url: bool = True,
        *,
        include_object_feature_hashes: Optional[typing.Set[str]] = None,
        include_classification_feature_hashes: Optional[typing.Set[str]] = None,
        include_reviews: bool = False,
        include_export_history: bool = False,
    ) -> LabelRow:
        """This function is documented in :meth:`encord.project.Project.get_label_row`."""
        payload = {
            "get_signed_url": get_signed_url,
            "multi_request": False,
            "include_object_feature_hashes": optional_set_to_list(include_object_feature_hashes),
            "include_classification_feature_hashes": optional_set_to_list(include_classification_feature_hashes),
            "include_reviews": include_reviews,
            "include_export_history": include_export_history,
        }

        return self._querier.basic_getter(LabelRow, uid, payload=payload, retryable=True)

    def get_label_rows(
        self,
        uids: List[str],
        get_signed_url: bool = True,
        *,
        include_object_feature_hashes: Optional[typing.Set[str]] = None,
        include_classification_feature_hashes: Optional[typing.Set[str]] = None,
        include_reviews: bool = False,
        include_export_history: bool = False,
    ) -> List[LabelRow]:
        """This function is documented in :meth:`encord.project.Project.get_label_rows`."""
        payload = {
            "get_signed_url": get_signed_url,
            "multi_request": True,
            "include_object_feature_hashes": optional_set_to_list(include_object_feature_hashes),
            "include_classification_feature_hashes": optional_set_to_list(include_classification_feature_hashes),
            "include_reviews": include_reviews,
            "include_export_history": include_export_history,
        }

        return self._querier.get_multiple(LabelRow, uids, payload=payload, retryable=True)

    def save_label_row(self, uid, label, validate_before_saving: bool = False):
        """This function is documented in :meth:`encord.project.Project.save_label_row`."""
        label = LabelRow(label)
        if validate_before_saving:
            label["validate_before_saving"] = True
        return self._querier.basic_setter(LabelRow, uid, payload=label, retryable=True)

    def save_label_rows(self, uids: List[str], payload: List[LabelRow], validate_before_saving: bool = False):
        """This function is meant for internal use, please consider using :class:`encord.objects.LabelRowV2` class instead

        Saves multiple label rows. See :meth:`.save_label_row`

        Args:
            uids: list of label hashes
            payload: list of LabelRow objects
            validate_before_saving: ????

        Returns:
            None
        """
        multirequest_payload = {
            "multi_request": True,
            "labels": payload,
            "validate_before_saving": validate_before_saving,
        }
        return self._querier.basic_setter(LabelRow, uid=uids, payload=multirequest_payload, retryable=True)

    def create_label_row(self, uid, *, get_signed_url=False) -> LabelRow:
        """This function is documented in :meth:`encord.project.Project.create_label_row`."""
        return self._querier.basic_put(LabelRow, uid=uid, payload={"get_signed_url": get_signed_url})

    def create_label_rows(
        self, uids: List[str], *, get_signed_url: bool = False, branch_name: Optional[str] = None
    ) -> List[LabelRow]:
        """This function is meant for internal use, please consider using :class:`encord.objects.LabelRowV2` class instead

        Create multiple label rows. See :meth:`.create_label_row`

        Args:
            uids: list of data uids where label_status is NOT_LABELLED.
            get_signed_url: bool whether to fetch the signed url for the internal label row
            branch_name: Optional[str] which branch name against which to create the label row
        Returns:
            List[LabelRow]: A list of created label rows
        """
        return self._querier.put_multiple(
            LabelRow,
            uid=uids,
            payload={"multi_request": True, "get_signed_url": get_signed_url, "branch_name": branch_name},
        )

    def add_datasets(self, dataset_hashes: List[str]) -> bool:
        """This function is documented in :meth:`encord.project.Project.add_datasets`."""
        payload = {"dataset_hashes": dataset_hashes}
        return self._querier.basic_setter(ProjectDataset, uid=None, payload=payload)

    def remove_datasets(self, dataset_hashes: List[str]) -> bool:
        """This function is documented in :meth:`encord.project.Project.remove_datasets`."""
        return self._querier.basic_delete(ProjectDataset, uid=dataset_hashes)

    def list_project_datasets(self, project_hash: UUID) -> Iterable[ProjectDataset]:
        return self._api_client.get(
            f"projects/{project_hash}/datasets", params=None, result_type=Page[ProjectDataset]
        ).results

    @deprecated("0.1.102", alternative="encord.ontology.Ontology class")
    def get_project_ontology(self) -> LegacyOntology:
        project = self.get_project()
        ontology = project["editor_ontology"]
        return LegacyOntology.from_dict(ontology)

    @deprecated("0.1.102", alternative="encord.ontology.Ontology class")
    def add_object(self, name: str, shape: ObjectShape) -> bool:
        """This function is documented in :meth:`encord.project.Project.add_object`."""
        if not name:
            raise ValueError("Ontology object name is empty")

        ontology = self.get_project_ontology()
        ontology.add_object(name, shape)
        return self.__set_project_ontology(ontology)

    @deprecated("0.1.102", alternative="encord.ontology.Ontology class")
    def add_classification(
        self,
        name: str,
        classification_type: ClassificationType,
        required: bool,
        options: Optional[Iterable[str]] = None,
    ):
        """This function is documented in :meth:`encord.project.Project.add_classification`."""
        if not name:
            raise ValueError("Ontology classification name is empty")

        ontology = self.get_project_ontology()
        ontology.add_classification(name, classification_type, required, options)
        return self.__set_project_ontology(ontology)

    def object_interpolation(
        self,
        key_frames,
        objects_to_interpolate,
    ):
        """This function is documented in :meth:`encord.project.Project.object_interpolation`."""
        if len(key_frames) == 0 or len(objects_to_interpolate) == 0:
            raise encord.exceptions.EncordException(
                message="To run object interpolation, you must pass key frames and objects to interpolate.."
            )

        interpolation_params = ObjectInterpolationParams(
            {
                "key_frames": key_frames,
                "objects_to_interpolate": objects_to_interpolate,
            }
        )

        algo = LabelingAlgorithm(
            {
                "algorithm_name": INTERPOLATION,
                "algorithm_parameters": interpolation_params,
            }
        )

        return self._querier.basic_setter(LabelingAlgorithm, str(uuid.uuid4()), payload=algo)

    def get_data(self, data_hash: str, get_signed_url: bool = False) -> Tuple[Optional[Video], Optional[List[Image]]]:
        """This function is documented in :meth:`encord.project.Project.get_data`."""
        uid = {"data_hash": data_hash, "get_signed_url": get_signed_url}

        dataset_data: DatasetData = self._querier.basic_getter(DatasetData, uid=uid)

        video: Union[Video, None] = None
        if dataset_data["video"] is not None:
            video = Video(dataset_data["video"])

        images: Union[List[Image], None] = None
        if dataset_data["images"] is not None:
            images = []

            for image in dataset_data["images"]:
                images.append(Image(image))

        return video, images

    def get_label_logs(
        self,
        user_hash: Optional[str] = None,
        data_hash: Optional[str] = None,
        from_unix_seconds: Optional[int] = None,
        to_unix_seconds: Optional[int] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        user_email: Optional[str] = None,
    ) -> List[LabelLog]:
        """This function is documented in :meth:`encord.project.Project.get_label_logs`."""
        if after is not None:
            if from_unix_seconds is not None:
                raise ValueError("Only one of 'from_unix_seconds' and 'after' parameters should be specified")

            from_unix_seconds = int(after.timestamp())

        if before is not None:
            if to_unix_seconds is not None:
                raise ValueError("Only one of 'to_unix_seconds' and 'before' parameters should be specified")

            to_unix_seconds = int(before.timestamp())

        payload = LabelLogParams(
            user_hash=user_hash,
            user_email=user_email,
            data_hash=data_hash,
            end_timestamp=to_unix_seconds,
            start_timestamp=from_unix_seconds,
        )

        return self._querier.get_multiple(LabelLog, payload=payload.to_dict(by_alias=False))

    def __set_project_ontology(self, ontology: LegacyOntology) -> bool:
        """Save updated project ontology
        Args:
            ontology: the updated project ontology

        Returns:
            bool
        """
        payload = {"editor": ontology.to_dict()}
        return self._querier.basic_setter(OrmProject, uid=None, payload=payload)

    def workflow_reopen(self, label_hashes: List[str]) -> None:
        """This function is documented in :meth:`encord.objects.LabelRowV2.workflow_reopen`."""
        self._querier.basic_setter(
            LabelWorkflowGraphNode,
            label_hashes,
            payload=LabelWorkflowGraphNodePayload(action=WorkflowAction.REOPEN),
        )

    def workflow_complete(self, label_hashes: List[str]) -> None:
        """This function is documented in :meth:`encord.objects.LabelRowV2.workflow_complete`."""
        self._querier.basic_setter(
            LabelWorkflowGraphNode,
            label_hashes,
            payload=LabelWorkflowGraphNodePayload(action=WorkflowAction.COMPLETE),
        )

    def workflow_set_priority(self, priorities: List[Tuple[str, float]]) -> None:
        self._api_client.post(
            f"projects/{self.project_hash}/priorities",
            params=None,
            payload=TaskPriorityParams(priorities=priorities),
            result_type=None,
        )

    def get_collaborator_timers(self, params: CollaboratorTimerParams) -> Iterable[CollaboratorTimer]:
        yield from self._api_client.get_paged_iterator(
            "analytics/collaborators/timers", params=params, result_type=CollaboratorTimer
        )

    def get_time_spent(self, params: TimeSpentParams) -> Iterable[TimeSpent]:
        yield from self._api_client.get_paged_iterator("analytics/time-spent", params=params, result_type=TimeSpent)

    def get_label_validation_errors(self, label_hash: str) -> List[str]:
        errors = self._api_client.get(
            f"projects/{self.project_hash}/labels/{label_hash}/validation-state",
            params=None,
            result_type=LabelValidationState,
        )

        if errors.is_valid:
            return []

        return errors.errors or []

    def active_import(self, project_mode: ActiveProjectMode, video_sampling_rate: Optional[float] = None) -> None:
        self._api_client.post(
            f"active/{self.project_hash}/import",
            params=None,
            payload=ActiveProjectImportPayload(project_mode=project_mode, video_sampling_rate=video_sampling_rate),
            result_type=None,
        )
        logger.info("Import initiated in Active, please check the app to see progress")

    def active_sync(self) -> None:
        self._api_client.post(
            f"active/{self.project_hash}/sync",
            params=None,
            payload=None,
            result_type=None,
        )
        logger.info("Sync initiated in Active, please check the app to see progress")

    def set_status(self, status: ProjectStatus) -> None:
        self._api_client.put(
            f"projects/{self.project_hash}/status",
            params=None,
            payload=SetProjectStatusPayload(status=status),
        )


CordClientProject = EncordClientProject
