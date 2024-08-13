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

import base64
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
from encord.configs import ENCORD_DOMAIN, ApiKeyConfig, BearerConfig, Config, EncordConfig, SshConfig
from encord.constants.enums import DataType
from encord.constants.model import AutomationModels, Device
from encord.constants.string_constants import (
    FITTED_BOUNDING_BOX,
    INTERPOLATION,
    TYPE_DATASET,
    TYPE_PROJECT,
)
from encord.exceptions import EncordException
from encord.http.constants import DEFAULT_REQUESTS_SETTINGS, RequestsSettings
from encord.http.querier import Querier
from encord.http.utils import (
    CloudUploadSettings,
    upload_images_to_encord,
    upload_to_signed_url_list,
    upload_video_to_encord,
)
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.analytics import (
    CollaboratorTimer,
    CollaboratorTimerParams,
)
from encord.orm.api_key import ApiKeyMeta
from encord.orm.bearer_request import BearerTokenResponse
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import (
    DEFAULT_DATASET_ACCESS_SETTINGS,
    AddPrivateDataResponse,
    Audio,
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
    SingleImage,
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
    LabelStatus,
    LabelValidationState,
    Review,
    ShadowDataState,
)
from encord.orm.labeling_algorithm import (
    BoundingBoxFittingParams,
    LabelingAlgorithm,
    ObjectInterpolationParams,
)
from encord.orm.model import (
    Model,
    ModelConfiguration,
    ModelInferenceParams,
    ModelOperations,
    ModelRow,
    ModelTrainingWeights,
    PublicModelTrainGetResultLongPollingStatus,
    PublicModelTrainGetResultParams,
    PublicModelTrainGetResultResponse,
    PublicModelTrainStartPayload,
    TrainingMetadata,
)
from encord.orm.project import (
    CopyDatasetAction,
    CopyDatasetOptions,
    CopyLabelsOptions,
    CopyProjectPayload,
    ProjectCopy,
    ProjectCopyOptions,
    ProjectDataset,
    ProjectUsers,
    TaskPriorityParams,
)
from encord.orm.project import Project as OrmProject
from encord.orm.project import ProjectDTO as ProjectOrmV2
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

logger = logging.getLogger(__name__)


class EncordClient:
    """
    Encord client. Allows you to query db items associated
    with a project (e.g. label rows, datasets).
    """

    def __init__(self, querier: Querier, config: Config, api_client: Optional[ApiClient] = None):
        self._querier = querier
        self._config = config
        self._api_client = api_client

    def _get_api_client(self) -> ApiClient:
        if not (isinstance(self._config, (SshConfig, BearerConfig))):
            raise EncordException(
                "This functionality requires private SSH key authentication. API keys are not supported."
            )

        if not self._api_client:
            raise RuntimeError("ApiClient should exist when authenticated with SSH key.")

        return self._api_client

    @staticmethod
    def initialise(
        resource_id: Optional[str] = None,
        api_key: Optional[str] = None,
        domain: str = ENCORD_DOMAIN,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
    ) -> Union[EncordClientProject, EncordClientDataset]:
        """
        Create and initialize a Encord client from a resource EntityId and API key.

        Args:
            resource_id: either of the following

                * A <project_hash>.
                  If ``None``, uses the ``ENCORD_PROJECT_ID`` environment variable.
                  The ``CORD_PROJECT_ID`` environment variable is supported for backwards compatibility.

                * A <dataset_hash>.
                  If ``None``, uses the ``ENCORD_DATASET_ID`` environment variable.
                  The ``CORD_DATASET_ID`` environment variable is supported for backwards compatibility.

            api_key: An API key.
                     If None, uses the ``ENCORD_API_KEY`` environment variable.
                     The ``CORD_API_KEY`` environment variable is supported for backwards compatibility.
            domain: The encord api-server domain.
                If None, the :obj:`encord.configs.ENCORD_DOMAIN` is used
            requests_settings: The RequestsSettings from this config

        Returns:
            EncordClient: A Encord client instance.
        """
        config = EncordConfig(resource_id, api_key, domain=domain, requests_settings=requests_settings)
        return EncordClient.initialise_with_config(config)

    @staticmethod
    def initialise_with_config(config: ApiKeyConfig) -> Union[EncordClientProject, EncordClientDataset]:
        """
        Create and initialize a Encord client from a Encord config instance.

        Args:
            config: A Encord config instance.

        Returns:
            EncordClient: A Encord client instance.
        """
        querier = Querier(config, resource_id=config.resource_id)
        key_type = querier.basic_getter(ApiKeyMeta)

        if key_type.resource_type == TYPE_PROJECT:
            logger.info("Initialising Encord client for project using key: %s", key_type.title)
            return EncordClientProject(querier, config)

        elif key_type.resource_type == TYPE_DATASET:
            logger.info("Initialising Encord client for dataset using key: %s", key_type.title)
            return EncordClientDataset(querier, config)

        else:
            raise encord.exceptions.InitialisationError(
                message=f"API key [{config.api_key}] is not associated with a project or dataset"
            )

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self._querier.get_multiple(CloudIntegration)

    def get_bearer_token(self) -> BearerTokenResponse:
        return self._get_api_client().get("user/bearer_token", None, result_type=BearerTokenResponse)


class EncordClientDataset(EncordClient):
    """
    DEPRECATED - prefer using the :class:`encord.dataset.Dataset` instead
    """

    def __init__(
        self,
        querier: Querier,
        config: Config,
        dataset_access_settings: DatasetAccessSettings = DEFAULT_DATASET_ACCESS_SETTINGS,
        api_client: Optional[ApiClient] = None,
    ):
        super().__init__(querier, config, api_client)
        self._dataset_access_settings = dataset_access_settings

    @staticmethod
    def initialise(
        resource_id: Optional[str] = None,
        api_key: Optional[str] = None,
        domain: str = ENCORD_DOMAIN,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
        dataset_access_settings: DatasetAccessSettings = DEFAULT_DATASET_ACCESS_SETTINGS,
    ) -> EncordClientDataset:
        """
        Create and initialize a Encord client from a resource EntityId and API key.

        Args:
            resource_id: either of the following

                * A <project_hash>.
                  If ``None``, uses the ``ENCORD_PROJECT_ID`` environment variable.
                  The ``CORD_PROJECT_ID`` environment variable is supported for backwards compatibility.

                * A <dataset_hash>.
                  If ``None``, uses the ``ENCORD_DATASET_ID`` environment variable.
                  The ``CORD_DATASET_ID`` environment variable is supported for backwards compatibility.

            api_key: An API key.
                     If None, uses the ``ENCORD_API_KEY`` environment variable.
                     The ``CORD_API_KEY`` environment variable is supported for backwards compatibility.
            domain: The encord api-server domain.
                If None, the :obj:`encord.configs.ENCORD_DOMAIN` is used
            requests_settings: The RequestsSettings from this config
            dataset_access_settings: Change the default :class:`encord.orm.dataset.DatasetAccessSettings`.

        Returns:
            EncordClientDataset: A Encord client dataset instance.
        """
        config = EncordConfig(resource_id, api_key, domain=domain, requests_settings=requests_settings)
        return EncordClientDataset.initialise_with_config(config, dataset_access_settings=dataset_access_settings)

    @staticmethod
    def initialise_with_config(
        config: ApiKeyConfig, dataset_access_settings: DatasetAccessSettings = DEFAULT_DATASET_ACCESS_SETTINGS
    ) -> EncordClientDataset:
        """
        Create and initialize a Encord client from a Encord config instance.

        Args:
            config: A Encord config instance.
            dataset_access_settings: Set the dataset_access_settings if you would like to change the defaults.

        Returns:
            EncordClientDataset: An Encord client dataset instance.
        """
        querier = Querier(config, resource_id=config.resource_id)
        key_type = querier.basic_getter(ApiKeyMeta)

        if key_type.resource_type == TYPE_PROJECT:
            raise RuntimeError("Trying to initialise an EncordClientDataset using a project key.")

        elif key_type.resource_type == TYPE_DATASET:
            logger.info("Initialising Encord client for dataset using key: %s", key_type.title)
            return EncordClientDataset(querier, config, dataset_access_settings=dataset_access_settings)

        else:
            raise encord.exceptions.InitialisationError(
                message=f"API key [{config.api_key}] is not associated with a project or dataset"
            )

    def get_dataset(self) -> OrmDataset:
        """
        Retrieve dataset info (pointers to data, labels).

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
        """
        Retrieve dataset rows (pointers to data, labels).

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
        """
        This function is documented in :meth:`encord.project.Dataset.add_users`.
        """

        payload = {"user_emails": user_emails, "user_role": user_role}
        users = self._querier.basic_setter(DatasetUsers, self._querier.resource_id, payload=payload)

        return [DatasetUser.from_dict(user) for user in users]

    def list_groups(self, dataset_hash: uuid.UUID) -> Page[DatasetGroup]:
        return self._get_api_client().get(
            f"datasets/{dataset_hash}/groups", params=None, result_type=Page[DatasetGroup]
        )

    def add_groups(self, dataset_hash: str, group_hash: List[uuid.UUID], user_role: DatasetUserRole) -> None:
        payload = AddDatasetGroupsPayload(group_hash_list=group_hash, user_role=user_role)
        self._get_api_client().post(f"datasets/{dataset_hash}/groups", params=None, payload=payload, result_type=None)

    def remove_groups(self, dataset_hash: uuid.UUID, group_hash: List[uuid.UUID]) -> None:
        params = RemoveGroupsParams(group_hash_list=group_hash)
        self._get_api_client().delete(f"datasets/{dataset_hash}/groups", params=params, result_type=None)

    def upload_video(
        self,
        file_path: Union[str, Path],
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        title: Optional[str] = None,
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> Video:
        """
        This function is documented in :meth:`encord.dataset.Dataset.upload_video`.
        """
        if os.path.exists(file_path):
            signed_urls = upload_to_signed_url_list(
                [file_path], self._config, self._querier, Video, cloud_upload_settings=cloud_upload_settings
            )
            res = upload_video_to_encord(signed_urls[0], title, folder_uuid, self._querier)
            if res:
                logger.info("Upload complete.")
                return Video(res)
            else:
                raise encord.exceptions.EncordException(message="An error has occurred during video upload.")
        else:
            raise encord.exceptions.EncordException(message=f"{file_path} does not point to a file.")

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
        """
        This function is documented in :meth:`encord.dataset.Dataset.create_image_group`.
        """
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise encord.exceptions.EncordException(message=f"{file_path} does not point to a file.")

        successful_uploads = upload_to_signed_url_list(
            file_paths, self._config, self._querier, Images, cloud_upload_settings=cloud_upload_settings
        )
        if not successful_uploads:
            raise encord.exceptions.EncordException("All image uploads failed. Image group was not created.")
        upload_images_to_encord(successful_uploads, self._querier)

        image_hash_list = [successful_upload.get("data_hash") for successful_upload in successful_uploads]
        payload = {
            "image_group_title": title,
            "create_video": create_video,
        }
        if folder_uuid is not None:
            payload["folder_uuid"] = str(folder_uuid)

        res = self._querier.basic_setter(
            ImageGroup,
            uid=image_hash_list,  # type: ignore
            payload=payload,
        )

        if res:
            titles = [video_data.get("title") for video_data in res]
            logger.info(f"Upload successful! {titles} created.")
            return [ImageGroup(obj) for obj in res]
        else:
            raise encord.exceptions.EncordException(message="An error has occurred during image group creation.")

    def create_dicom_series(
        self,
        file_paths: typing.Collection[Union[Path, str]],
        title: Optional[str] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> Dict:
        """
        This function is documented in :meth:`encord.dataset.Dataset.create_dicom_series`.
        """
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise encord.exceptions.EncordException(message=f"{file_path} does not point to a file.")

        successful_uploads = upload_to_signed_url_list(
            file_paths=file_paths,
            config=self._config,
            querier=self._querier,
            orm_class=DicomSeries,
            cloud_upload_settings=cloud_upload_settings,
        )
        if not successful_uploads:
            raise encord.exceptions.EncordException("DICOM files upload failed. The DICOM series was not created.")

        dicom_files = [
            {
                "id": file["data_hash"],
                "uri": file["file_link"],
                "title": file["title"],
            }
            for file in successful_uploads
        ]

        payload = {
            "title": title,
        }

        if folder_uuid is not None:
            payload["folder_uuid"] = str(folder_uuid)

        res = self._querier.basic_setter(DicomSeries, uid=dicom_files, payload=payload)
        if not res:
            raise encord.exceptions.EncordException(message="An error has occurred during the DICOM series creation.")

        return res

    def upload_image(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> Image:
        """
        This function is documented in :meth:`encord.dataset.Dataset.upload_image`.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if not file_path.is_file():
            raise encord.exceptions.EncordException(message=f"{str(file_path)} does not point to a file.")

        successful_uploads = upload_to_signed_url_list(
            [str(file_path)], self._config, self._querier, Images, cloud_upload_settings=cloud_upload_settings
        )
        if not successful_uploads:
            raise encord.exceptions.EncordException("Image upload failed.")

        upload = successful_uploads[0]
        if folder_uuid is not None:
            upload["folder_uuid"] = str(folder_uuid)
        if title is not None:
            upload["title"] = title

        res = self._querier.basic_setter(SingleImage, uid=None, payload=upload)

        if res["success"]:
            return Image({"data_hash": upload["data_hash"], "title": upload["title"], "file_link": upload["file_link"]})
        else:
            raise encord.exceptions.EncordException("Image upload failed.")

    def upload_audio(
        self,
        file_path: Union[str, Path],
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        title: Optional[str] = None,
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> Audio:
        if os.path.exists(file_path):
            signed_urls = upload_to_signed_url_list(
                [file_path], self._config, self._querier, Audio, cloud_upload_settings=cloud_upload_settings
            )
            res = upload_video_to_encord(signed_urls[0], title, folder_uuid, self._querier)
            if res:
                logger.info("Upload complete.")
                return Audio(res)
            else:
                raise encord.exceptions.EncordException(message="An error has occurred during audio upload.")
        else:
            raise encord.exceptions.EncordException(message=f"{file_path} does not point to a file.")

    def link_items(
        self,
        item_uuids: List[uuid.UUID],
        duplicates_behavior: DataLinkDuplicatesBehavior = DataLinkDuplicatesBehavior.SKIP,
    ) -> List[DataRow]:
        """
        Link storage items to the dataset, creating new data rows.

        Args:
            item_uuids: List of item UUIDs to link to the dataset
            duplicates_behaviour: The behavior to follow when encountering duplicates. Defaults to `SKIP`. See also
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

    def delete_image_group(self, data_hash: str):
        """
        This function is documented in :meth:`encord.dataset.Dataset.delete_image_group`.
        """
        self._querier.basic_delete(ImageGroup, uid=data_hash)

    def delete_data(self, data_hashes: Union[List[str], str]):
        """
        This function is documented in :meth:`encord.dataset.Dataset.delete_data`.
        """
        if isinstance(data_hashes, str):
            data_hashes = [data_hashes]
        self._querier.basic_delete(Video, uid=data_hashes)

    def add_private_data_to_dataset(
        self,
        integration_id: str,
        private_files: Union[str, typing.Dict, Path, typing.TextIO],
        ignore_errors: bool = False,
    ) -> AddPrivateDataResponse:
        """
        This function is documented in :meth:`encord.dataset.Dataset.add_private_data_to_dataset`.
        """
        upload_job_id = self.add_private_data_to_dataset_start(
            integration_id,
            private_files,
            ignore_errors,
        )

        res = self.add_private_data_to_dataset_get_result(upload_job_id)

        if res.status == LongPollingStatus.DONE:
            return AddPrivateDataResponse(dataset_data_list=res.data_hashes_with_titles)
        elif res.status == LongPollingStatus.ERROR:
            raise encord.exceptions.EncordException(f"add_private_data_to_dataset errors occurred {res.errors}")
        else:
            raise ValueError(f"res.status={res.status}, this should never happen")

    def add_private_data_to_dataset_start(
        self,
        integration_id: str,
        private_files: Union[str, typing.Dict, Path, typing.TextIO],
        ignore_errors: bool = False,
        folder_uuid: Optional[uuid.UUID] = None,
    ) -> str:
        """
        This function is documented in :meth:`encord.dataset.Dataset.add_private_data_to_dataset_start`.
        """
        if isinstance(private_files, dict):
            files = private_files
        elif isinstance(private_files, str):
            if os.path.exists(private_files):
                text_contents = Path(private_files).read_text(encoding="utf-8")
            else:
                text_contents = private_files

            files = json.loads(text_contents)
        elif isinstance(private_files, Path):
            text_contents = private_files.read_text(encoding="utf-8")
            files = json.loads(text_contents)
        elif isinstance(private_files, typing.TextIO):
            text_contents = private_files.read()
            files = json.loads(text_contents)
        else:
            raise ValueError(f"Type [{type(private_files)}] of argument private_files is not supported")

        payload = {
            "files": files,
            "integration_id": integration_id,
            "ignore_errors": ignore_errors,
        }
        if folder_uuid is not None:
            payload["folder_uuid"] = str(folder_uuid)

        process_hash = self._querier.basic_setter(
            DatasetDataLongPolling,
            self._querier.resource_id,
            payload=payload,
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
        """
        This function is documented in :meth:`encord.dataset.Dataset.add_private_data_to_dataset_get_result`.
        """
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

    def update_data_item(self, data_hash: str, new_title: str) -> bool:
        """This function is documented in :meth:`encord.dataset.Dataset.update_data_item`."""
        payload = [{"video_hash": data_hash, "title": new_title}]

        response = self._querier.basic_setter(Video, self.get_dataset().dataset_hash, payload=payload)
        try:
            return response.get("success", False)
        except AttributeError:
            return False

    def re_encode_data(self, data_hashes: List[str]):
        """
        This function is documented in :meth:`encord.dataset.Dataset.re_encode_data`.
        """
        payload = {"data_hash": data_hashes}
        return self._querier.basic_put(ReEncodeVideoTask, uid=None, payload=payload)

    def re_encode_data_status(self, job_id: int):
        """
        This function is documented in :meth:`encord.dataset.Dataset.re_encode_data_status`.
        """
        return self._querier.basic_getter(ReEncodeVideoTask, uid=job_id)

    def run_ocr(self, image_group_id: str) -> List[ImageGroupOCR]:
        """
        This function is documented in :meth:`encord.dataset.Dataset.run_ocr`.
        """

        payload = {"image_group_data_hash": image_group_id}
        return self._querier.get_multiple(ImageGroupOCR, payload=payload)


class EncordClientProject(EncordClient):
    """
    DEPRECATED - prefer using the :class:`encord.project.Project` instead
    """

    @property
    def project_hash(self) -> str:
        assert self._querier.resource_id, "Resource id can't be empty for created project client"
        return self._querier.resource_id  # type: ignore[attr-defined]

    def get_project(self, include_labels_metadata=True) -> OrmProject:
        """
        Retrieve project info (pointers to data, labels).

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
        """
        This is an internal method, do not use it directly.
        Use :meth:`UserClient.get_project` instead.
        """
        return self._get_api_client().get(f"/projects/{self.project_hash}", params=None, result_type=ProjectOrmV2)

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
    ) -> List[LabelRowMetadata]:
        """
        This function is documented in :meth:`encord.project.Project.list_label_rows`.
        """

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
        }
        return self._querier.get_multiple(LabelRowMetadata, payload=payload, retryable=True)

    def set_label_status(self, label_hash: str, label_status: LabelStatus) -> bool:
        """
        This function is documented in :meth:`encord.project.Project.set_label_status`.
        """
        payload = {
            "label_status": label_status.value,
        }
        return self._querier.basic_setter(LabelStatus, label_hash, payload)

    def add_users(self, user_emails: List[str], user_role: ProjectUserRole) -> List[ProjectUser]:
        """
        This function is documented in :meth:`encord.project.Project.add_users`.
        """

        payload = {"user_emails": user_emails, "user_role": user_role}
        users = self._querier.basic_setter(ProjectUsers, self._querier.resource_id, payload=payload)

        return [ProjectUser.from_dict(user) for user in users]

    def list_groups(self, project_hash: uuid.UUID) -> Page[ProjectGroup]:
        return self._get_api_client().get(
            f"projects/{project_hash}/groups", params=None, result_type=Page[ProjectGroup]
        )

    def add_groups(self, project_hash: uuid.UUID, group_hash: List[uuid.UUID], user_role: ProjectUserRole) -> None:
        payload = AddProjectGroupsPayload(group_hash_list=group_hash, user_role=user_role)
        self._get_api_client().post(f"projects/{project_hash}/groups", params=None, payload=payload, result_type=None)

    def remove_groups(self, group_hash: List[uuid.UUID]) -> None:
        params = RemoveGroupsParams(group_hash_list=group_hash)
        self._get_api_client().delete(f"projects/{self.project_hash}/groups", params=params, result_type=None)

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
        """
        This function is documented in :meth:`encord.project.Project.copy_project`.
        """
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
        """
        This function is documented in :meth:`encord.project.Project.get_label_row`.
        """
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
        """
        This function is documented in :meth:`encord.project.Project.get_label_rows`.
        """
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
        """
        This function is documented in :meth:`encord.project.Project.save_label_row`.
        """
        label = LabelRow(label)
        if validate_before_saving:
            label["validate_before_saving"] = True
        return self._querier.basic_setter(LabelRow, uid, payload=label, retryable=True)

    def save_label_rows(self, uids: List[str], payload: List[LabelRow], validate_before_saving: bool = False):
        """
        This function is meant for internal use, please consider using :class:`encord.objects.LabelRowV2` class instead

        Saves multiple label rows. See :meth:`.save_label_row`

        Args:
            uids: list of label hashes
            payload: list of LabelRow objects

        Returns:
            None
        """
        multirequest_payload = {
            "multi_request": True,
            "labels": payload,
            "validate_before_saving": validate_before_saving,
        }
        return self._querier.basic_setter(LabelRow, uid=uids, payload=multirequest_payload, retryable=True)

    def create_label_row(self, uid, *, get_signed_url=False) -> typing.Any:
        """
        This function is documented in :meth:`encord.project.Project.create_label_row`.
        """
        return self._querier.basic_put(LabelRow, uid=uid, payload={"get_signed_url": get_signed_url})

    def create_label_rows(self, uids: List[str], *, get_signed_url=False) -> List[LabelRow]:
        """
        This function is meant for internal use, please consider using :class:`encord.objects.LabelRowV2` class instead

        Create multiple label rows. See :meth:`.create_label_row`

        Args:
            uids: list of data uids where label_status is NOT_LABELLED.

        Returns:
            List[LabelRow]: A list of created label rows
        """
        return self._querier.put_multiple(
            LabelRow, uid=uids, payload={"multi_request": True, "get_signed_url": get_signed_url}
        )

    def submit_label_row_for_review(self, uid):
        """
        This function is documented in :meth:`encord.project.Project.submit_label_row_for_review`.
        """
        return self._querier.basic_put(Review, uid=uid, payload=None)

    def add_datasets(self, dataset_hashes: List[str]) -> bool:
        """
        This function is documented in :meth:`encord.project.Project.add_datasets`.
        """
        payload = {"dataset_hashes": dataset_hashes}
        return self._querier.basic_setter(ProjectDataset, uid=None, payload=payload)

    def remove_datasets(self, dataset_hashes: List[str]) -> bool:
        """
        This function is documented in :meth:`encord.project.Project.remove_datasets`.
        """
        return self._querier.basic_delete(ProjectDataset, uid=dataset_hashes)

    def list_project_datasets(self, project_hash: UUID) -> Iterable[ProjectDataset]:
        return (
            self._get_api_client()
            .get(f"projects/{project_hash}/datasets", params=None, result_type=Page[ProjectDataset])
            .results
        )

    def get_project_ontology(self) -> LegacyOntology:
        project = self.get_project()
        ontology = project["editor_ontology"]
        return LegacyOntology.from_dict(ontology)

    @deprecated("0.1.102", alternative="encord.ontology.Ontology class")
    def add_object(self, name: str, shape: ObjectShape) -> bool:
        """
        This function is documented in :meth:`encord.project.Project.add_object`.
        """
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
        """
        This function is documented in :meth:`encord.project.Project.add_classification`.
        """
        if not name:
            raise ValueError("Ontology classification name is empty")

        ontology = self.get_project_ontology()
        ontology.add_classification(name, classification_type, required, options)
        return self.__set_project_ontology(ontology)

    def list_models(self) -> List[ModelConfiguration]:
        """
        This function is documented in :meth:`encord.project.Project.list_models`.
        """
        return self._querier.get_multiple(ModelConfiguration)

    def get_training_metadata(
        self,
        model_iteration_uids: Iterable[str],
        get_created_at: bool = False,
        get_training_final_loss: bool = False,
        get_model_training_labels: bool = False,
    ) -> List[TrainingMetadata]:
        """
        This function is documented in :meth:`encord.project.Project.get_training_metadata`.
        """
        payload = {
            "model_iteration_uids": list(model_iteration_uids),
            "get_created_at": get_created_at,
            "get_training_final_loss": get_training_final_loss,
            "get_model_training_labels": get_model_training_labels,
        }
        return self._querier.get_multiple(TrainingMetadata, payload=payload)

    def create_model_row(
        self,
        title: str,
        description: str,
        features: List[str],
        model: Union[AutomationModels, str],
    ) -> str:
        """
        This function is documented in :meth:`encord.project.Project.create_model_row`.
        """
        if title is None:
            raise encord.exceptions.EncordException(message="You must set a title to create a model row.")

        if features is None:
            raise encord.exceptions.EncordException(
                message="You must pass a list of feature uid's (hashes) to create a model row."
            )

        if isinstance(model, AutomationModels):
            model = model.value

        elif model is None or not AutomationModels.has_value(model):  # Backward compatibility with string options
            raise encord.exceptions.EncordException(
                message="You must pass a model from the `encord.constants.model.AutomationModels` Enum to create a "
                "model row."
            )

        model_row = ModelRow(
            {
                "title": title,
                "description": description,
                "features": features,
                "model": model,
            }
        )

        model_payload = Model(
            {
                "model_operation": ModelOperations.CREATE.value,
                "model_parameters": model_row,
            }
        )

        return self._querier.basic_put(Model, None, payload=model_payload)

    def model_delete(self, uid: str) -> bool:
        """
        This function is documented in :meth:`encord.project.Project.model_delete`.
        """

        return self._querier.basic_delete(Model, uid=uid)

    def model_inference(
        self,
        uid: str,
        file_paths: Optional[List[str]] = None,
        base64_strings: Optional[List[bytes]] = None,
        conf_thresh: float = 0.6,
        iou_thresh: float = 0.3,
        device: Device = Device.CUDA,
        detection_frame_range: Optional[List[int]] = None,
        allocation_enabled: bool = False,
        data_hashes: Optional[List[str]] = None,
        rdp_thresh: float = 0.005,
    ):
        """
        This function is documented in :meth:`encord.project.Project.model_inference`.
        """
        if (file_paths is None and base64_strings is None and data_hashes is None) or (
            file_paths is not None
            and len(file_paths) > 0
            and base64_strings is not None
            and len(base64_strings) > 0
            and data_hashes is not None
            and len(data_hashes) > 0
        ):
            raise encord.exceptions.EncordException(
                message="To run model inference, you must pass either a list of files or base64 strings or list of"
                " data hash."
            )

        if detection_frame_range is None:
            detection_frame_range = []

        files = []
        if file_paths is not None:
            for file_path in file_paths:
                file = open(file_path, "rb").read()
                files.append(
                    {
                        "uid": file_path,  # Add file path as inference identifier
                        "base64_str": base64.b64encode(file).decode("utf-8"),  # File to base64 string
                    }
                )

        elif base64_strings is not None:
            for base64_string in base64_strings:
                files.append(
                    {
                        "uid": str(uuid.uuid4()),  # Add uuid as inference identifier
                        "base64_str": base64_string.decode("utf-8"),  # base64 string to utf-8
                    }
                )

        inference_params = ModelInferenceParams(
            {
                "files": files,
                "conf_thresh": conf_thresh,
                "iou_thresh": iou_thresh,
                "device": _device_to_string(device),
                "detection_frame_range": detection_frame_range,
                "allocation_enabled": allocation_enabled,
                "data_hashes": data_hashes,
                "rdp_thresh": rdp_thresh,
            }
        )

        model = Model(
            {
                "model_operation": ModelOperations.INFERENCE.value,
                "model_parameters": inference_params,
            }
        )

        return self._querier.basic_setter(Model, uid, payload=model)

    def model_train_start(
        self,
        model_hash: Union[str, UUID],
        label_rows: List[Union[str, UUID]],
        epochs: int,
        weights: ModelTrainingWeights,
        batch_size: int = 24,
        device: Device = Device.CUDA,
    ) -> UUID:
        """
        This function is documented in :meth:`encord.project.Project.model_train_start`.
        """

        if not label_rows:
            raise encord.exceptions.EncordException(
                message="You must pass a list of label row uid's (hashes) to train a model."
            )

        if not epochs:
            raise encord.exceptions.EncordException(message="You must set number of epochs to train a model.")

        if not batch_size:
            raise encord.exceptions.EncordException(message="You must set a batch size to train a model.")

        if weights is None or not isinstance(weights, ModelTrainingWeights):
            raise encord.exceptions.EncordException(
                message="You must pass weights from the `encord.constants.model_weights` module to train a model."
            )

        training_hash = self._get_api_client().post(
            f"ml-models/{model_hash}/training",
            params=None,
            payload=PublicModelTrainStartPayload(
                label_rows=[x if isinstance(x, UUID) else UUID(x) for x in label_rows],
                epochs=epochs,
                batch_size=batch_size,
                model=weights.model,
                training_weights_link=weights.training_weights_link,
                device=_device_to_string(device),
            ),
            result_type=UUID,
        )

        logger.info(f"model_train job started with training_hash={training_hash}.")
        logger.info("SDK process can be terminated, this will not affect successful job execution.")
        logger.info("You can follow the progress in the SDK using model_train_get_result method.")
        logger.info("You can also follow the progress in the web app via notifications.")

        return training_hash

    def model_train_get_result(
        self,
        model_hash: Union[str, UUID],
        training_hash: Union[str, UUID],
        timeout_seconds: int = 7 * 24 * 60 * 60,  # 7 days
    ) -> dict:
        """
        This function is documented in :meth:`encord.project.Project.model_train_get_result`.
        """

        failed_requests_count = 0
        polling_start_timestamp = time.perf_counter()

        while True:
            try:
                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                logger.info(f"__model_train_get_result started polling call {polling_elapsed_seconds=}")
                tmp_res = self._get_api_client().get(
                    f"ml-models/{model_hash}/{training_hash}/training",
                    params=PublicModelTrainGetResultParams(
                        timeout_seconds=min(
                            polling_available_seconds,
                            LONG_POLLING_MAX_REQUEST_TIME_SECONDS,
                        ),
                    ),
                    result_type=PublicModelTrainGetResultResponse,
                )

                if tmp_res.status == PublicModelTrainGetResultLongPollingStatus.DONE:
                    logger.info(f"model_train job completed with training_hash={training_hash}.")

                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                if polling_available_seconds == 0 or tmp_res.status in [
                    PublicModelTrainGetResultLongPollingStatus.DONE,
                    PublicModelTrainGetResultLongPollingStatus.ERROR,
                ]:
                    res = tmp_res
                    break

                failed_requests_count = 0
            except (requests.exceptions.RequestException, encord.exceptions.RequestException):
                failed_requests_count += 1

                if failed_requests_count >= LONG_POLLING_RESPONSE_RETRY_N:
                    raise

                time.sleep(LONG_POLLING_SLEEP_ON_FAILURE_SECONDS)

        if res.status == PublicModelTrainGetResultLongPollingStatus.DONE:
            if res.result is None:
                raise ValueError(f"{res.status=}, res.result should not be None with DONE status")

            return res.result.dict()
        elif res.status == PublicModelTrainGetResultLongPollingStatus.ERROR:
            raise encord.exceptions.EncordException("model_train error occurred")
        else:
            raise ValueError(
                f"res.status={res.status}, only DONE and ERROR status is expected after successful long polling"
            )

    def object_interpolation(
        self,
        key_frames,
        objects_to_interpolate,
    ):
        """
        This function is documented in :meth:`encord.project.Project.object_interpolation`.
        """
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

    def fitted_bounding_boxes(
        self,
        frames: dict,
        video: dict,
    ):
        """
        This function is documented in :meth:`encord.project.Project.fitted_bounding_boxes`.
        """
        if len(frames) == 0 or len(video) == 0:
            raise encord.exceptions.EncordException(
                message="To run fitting, you must pass frames and video to run bounding box fitting on.."
            )

        fitting_params = BoundingBoxFittingParams(
            {
                "labels": frames,
                "video": video,
            }
        )

        algo = LabelingAlgorithm(
            {
                "algorithm_name": FITTED_BOUNDING_BOX,
                "algorithm_parameters": fitting_params,
            }
        )

        return self._querier.basic_setter(LabelingAlgorithm, str(uuid.uuid4()), payload=algo)

    def get_data(self, data_hash: str, get_signed_url: bool = False) -> Tuple[Optional[Video], Optional[List[Image]]]:
        """
        This function is documented in :meth:`encord.project.Project.get_data`.
        """
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
        """
        This function is documented in :meth:`encord.project.Project.get_label_logs`.
        """
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
        """
        Save updated project ontology
        Args:
            ontology: the updated project ontology

        Returns:
            bool
        """
        payload = {"editor": ontology.to_dict()}
        return self._querier.basic_setter(OrmProject, uid=None, payload=payload)

    def workflow_reopen(self, label_hashes: List[str]) -> None:
        """
        This function is documented in :meth:`encord.objects.LabelRowV2.workflow_reopen`.
        """
        self._querier.basic_setter(
            LabelWorkflowGraphNode,
            label_hashes,
            payload=LabelWorkflowGraphNodePayload(action=WorkflowAction.REOPEN),
        )

    def workflow_complete(self, label_hashes: List[str]) -> None:
        """
        This function is documented in :meth:`encord.objects.LabelRowV2.workflow_complete`.
        """
        self._querier.basic_setter(
            LabelWorkflowGraphNode,
            label_hashes,
            payload=LabelWorkflowGraphNodePayload(action=WorkflowAction.COMPLETE),
        )

    def workflow_set_priority(self, priorities: List[Tuple[str, float]]) -> None:
        self._get_api_client().post(
            f"projects/{self.project_hash}/priorities",
            params=None,
            payload=TaskPriorityParams(priorities=priorities),
            result_type=None,
        )

    def get_collaborator_timers(self, params: CollaboratorTimerParams) -> Iterable[CollaboratorTimer]:
        yield from self._get_api_client().get_paged_iterator(
            "analytics/collaborators/timers", params=params, result_type=CollaboratorTimer
        )

    def get_label_validation_errors(self, label_hash: str) -> List[str]:
        errors = self._get_api_client().get(
            f"projects/{self.project_hash}/labels/{label_hash}/validation-state",
            params=None,
            result_type=LabelValidationState,
        )

        if errors.is_valid:
            return []

        return errors.errors or []


def _device_to_string(device: Device) -> str:
    if not isinstance(device, Device):
        if device is None or not Device.has_value(device):  # Backward compatibility with string options
            raise EncordException(message="You must pass a device from the `from encord.constants.model.Device` enum.")
        return cast(str, device)

    return device.value


CordClientProject = EncordClientProject
