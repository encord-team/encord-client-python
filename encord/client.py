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

""" ``encord.client`` provides a simple Python client that allows you
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
import typing
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union

import encord.exceptions
from encord.configs import ENCORD_DOMAIN, ApiKeyConfig, Config, EncordConfig
from encord.constants.model import AutomationModels, Device
from encord.constants.string_constants import *
from encord.http.constants import DEFAULT_REQUESTS_SETTINGS, RequestsSettings
from encord.http.querier import Querier
from encord.http.utils import (
    CloudUploadSettings,
    upload_images_to_encord,
    upload_to_signed_url_list,
    upload_video_to_encord,
)
from encord.orm.api_key import ApiKeyMeta
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import DEFAULT_DATASET_ACCESS_SETTINGS, AddPrivateDataResponse
from encord.orm.dataset import Dataset as OrmDataset
from encord.orm.dataset import (
    DatasetAccessSettings,
    DatasetData,
    DatasetUser,
    DatasetUserRole,
    DatasetUsers,
    DicomSeries,
    Image,
    ImageGroup,
    ImageGroupOCR,
    Images,
    ReEncodeVideoTask,
    SingleImage,
    Video,
)
from encord.orm.label_log import LabelLog
from encord.orm.label_row import (
    AnnotationTaskStatus,
    LabelRow,
    LabelRowMetadata,
    LabelStatus,
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
    ModelTrainingParams,
    ModelTrainingWeights,
    TrainingMetadata,
)
from encord.orm.project import (
    CopyDatasetAction,
    CopyDatasetOptions,
    CopyLabelsOptions,
    CopyProjectPayload,
)
from encord.orm.project import Project as OrmProject
from encord.orm.project import (
    ProjectCopy,
    ProjectCopyOptions,
    ProjectDataset,
    ProjectUsers,
)
from encord.project_ontology.classification_type import ClassificationType
from encord.project_ontology.object_type import ObjectShape
from encord.project_ontology.ontology import Ontology
from encord.utilities.client_utilities import optional_set_to_list, parse_datetime
from encord.utilities.project_user import ProjectUser, ProjectUserRole

logger = logging.getLogger(__name__)


class EncordClient(object):
    """
    Encord client. Allows you to query db items associated
    with a project (e.g. label rows, datasets).
    """

    def __init__(self, querier: Querier, config: Config):
        self._querier = querier
        self._config: Config = config

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
        querier = Querier(config)
        key_type = querier.basic_getter(ApiKeyMeta)
        resource_type = key_type.get("resource_type", None)

        if resource_type == TYPE_PROJECT:
            logger.info("Initialising Encord client for project using key: %s", key_type.get("title", ""))
            return EncordClientProject(querier, config)

        elif resource_type == TYPE_DATASET:
            logger.info("Initialising Encord client for dataset using key: %s", key_type.get("title", ""))
            return EncordClientDataset(querier, config)

        else:
            raise encord.exceptions.InitialisationError(
                message=f"API key [{config.api_key}] is not associated with a project or dataset"
            )

    def __getattr__(self, name):
        """Overriding __getattr__."""
        value = self.__dict__.get(name)
        if not value:
            self_type = type(self).__name__
            if self_type == "CordClientDataset" and name in EncordClientProject.__dict__.keys():
                raise encord.exceptions.EncordException(
                    message=("{} is implemented in Projects, not Datasets.".format(name))
                )
            elif self_type == "CordClientProject" and name in EncordClientDataset.__dict__.keys():
                raise encord.exceptions.EncordException(
                    message=("{} is implemented in Datasets, not Projects.".format(name))
                )
            elif name == "items":
                pass
            else:
                raise encord.exceptions.EncordException(message="{} is not implemented.".format(name))
        return value

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self._querier.get_multiple(CloudIntegration)


CordClient = EncordClient


class EncordClientDataset(EncordClient):
    """
    DEPRECATED - prefer using the :class:`encord.dataset.Dataset` instead
    """

    def __init__(
        self,
        querier: Querier,
        config: Config,
        dataset_access_settings: DatasetAccessSettings = DEFAULT_DATASET_ACCESS_SETTINGS,
    ):
        super().__init__(querier, config)
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
    ) -> Union[EncordClientProject, EncordClientDataset]:
        """
        Create and initialize a Encord client from a Encord config instance.

        Args:
            config: A Encord config instance.
            dataset_access_settings: Set the dataset_access_settings if you would like to change the defaults.

        Returns:
            EncordClientDataset: An Encord client dataset instance.
        """
        querier = Querier(config)
        key_type = querier.basic_getter(ApiKeyMeta)
        resource_type = key_type.get("resource_type", None)

        if resource_type == TYPE_PROJECT:
            raise RuntimeError("Trying to initialise an EncordClientDataset using a project key.")

        elif resource_type == TYPE_DATASET:
            logger.info("Initialising Encord client for dataset using key: %s", key_type.get("title", ""))
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
            OrmDataset, payload={"dataset_access_settings": dataclasses.asdict(self._dataset_access_settings)}
        )

        for row in res.data_rows:
            row["_querier"] = self._querier
        return res

    def set_access_settings(self, dataset_access_settings=DatasetAccessSettings) -> None:
        self._dataset_access_settings = dataset_access_settings

    def add_users(self, user_emails: List[str], user_role: DatasetUserRole) -> List[DatasetUser]:
        """
        This function is documented in :meth:`encord.project.Dataset.add_users`.
        """

        payload = {"user_emails": user_emails, "user_role": user_role}

        users = self._querier.basic_setter(DatasetUsers, self._config.resource_id, payload=payload)

        return list(map(lambda user: DatasetUser.from_dict(user), users))

    def upload_video(
        self,
        file_path: str,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        title: Optional[str] = None,
    ):
        """
        This function is documented in :meth:`encord.dataset.Dataset.upload_video`.
        """
        if os.path.exists(file_path):
            signed_urls = upload_to_signed_url_list(
                [file_path], self._config, self._querier, Video, cloud_upload_settings=cloud_upload_settings
            )
            res = upload_video_to_encord(signed_urls[0], title, self._querier)
            if res:
                logger.info("Upload complete.")
                return res
            else:
                raise encord.exceptions.EncordException(message="An error has occurred during video upload.")
        else:
            raise encord.exceptions.EncordException(message="{} does not point to a file.".format(file_path))

    def create_image_group(
        self,
        file_paths: List[str],
        max_workers: Optional[int] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        title: Optional[str] = None,
        *,
        create_video: bool = True,
    ):
        """
        This function is documented in :meth:`encord.dataset.Dataset.create_image_group`.
        """
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise encord.exceptions.EncordException(message="{} does not point to a file.".format(file_path))

        successful_uploads = upload_to_signed_url_list(
            file_paths, self._config, self._querier, Images, cloud_upload_settings=cloud_upload_settings
        )
        if not successful_uploads:
            raise encord.exceptions.EncordException("All image uploads failed. Image group was not created.")
        upload_images_to_encord(successful_uploads, self._querier)

        image_hash_list = [successful_upload.get("data_hash") for successful_upload in successful_uploads]
        res = self._querier.basic_setter(
            ImageGroup,
            uid=image_hash_list,
            payload={
                "image_group_title": title,
                "create_video": create_video,
            },
        )

        if res:
            titles = [video_data.get("title") for video_data in res]
            logger.info("Upload successful! {} created.".format(titles))
            return res
        else:
            raise encord.exceptions.EncordException(message="An error has occurred during image group creation.")

    def create_dicom_series(
        self,
        file_paths: List[str],
        title: Optional[str] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ):
        """
        This function is documented in :meth:`encord.dataset.Dataset.create_dicom_series`.
        """
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise encord.exceptions.EncordException(message="{} does not point to a file.".format(file_path))

        successful_uploads = upload_to_signed_url_list(
            file_paths=file_paths,
            config=self._config,
            querier=self._querier,
            orm_class=DicomSeries,
            cloud_upload_settings=cloud_upload_settings,
        )
        if not successful_uploads:
            raise encord.exceptions.EncordException("All image uploads failed. Image group was not created.")

        dicom_files = [
            {
                "id": file["data_hash"],
                "uri": file["file_link"],
                "title": file["title"],
            }
            for file in successful_uploads
        ]

        res = self._querier.basic_setter(DicomSeries, uid=dicom_files, payload={"title": title})

        if res:
            return res
        else:
            raise encord.exceptions.EncordException(message="An error has occurred during image group creation.")

    def upload_image(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
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
        if title is not None:
            upload["title"] = title

        res = self._querier.basic_setter(SingleImage, uid=None, payload=upload)

        if res["success"]:
            return Image({"data_hash": upload["data_hash"], "title": upload["title"], "file_link": upload["file_link"]})
        else:
            raise encord.exceptions.EncordException("Image upload failed.")

    def delete_image_group(self, data_hash: str):
        """
        This function is documented in :meth:`encord.dataset.Dataset.delete_image_group`.
        """
        self._querier.basic_delete(ImageGroup, uid=data_hash)

    def delete_data(self, data_hashes: List[str]):
        """
        This function is documented in :meth:`encord.dataset.Dataset.delete_data`.
        """
        self._querier.basic_delete(Video, uid=data_hashes)

    def add_private_data_to_dataset(
        self,
        integration_id: str,
        private_files: Union[str, typing.Dict, Path, typing.TextIO],
        ignore_errors: bool = False,
    ) -> AddPrivateDataResponse:
        """
        This function is documented in :meth:`encord.dataset.Dataset.AddPrivateDataResponse`.
        """
        if isinstance(private_files, dict):
            files = private_files
        elif isinstance(private_files, str):
            if os.path.exists(private_files):
                text_contents = Path(private_files).read_text()
            else:
                text_contents = private_files

            files = json.loads(text_contents)
        elif isinstance(private_files, Path):
            text_contents = private_files.read_text()
            files = json.loads(text_contents)
        elif isinstance(private_files, typing.TextIO):
            text_contents = private_files.read()
            files = json.loads(text_contents)
        else:
            raise ValueError(f"Type [{type(private_files)}] of argument private_files is not supported")

        payload = {"files": files, "integration_id": integration_id, "ignore_errors": ignore_errors}
        response = self._querier.basic_setter(DatasetData, self._config.resource_id, payload=payload)

        return AddPrivateDataResponse.from_dict(response)

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

        response = self._querier.get_multiple(ImageGroupOCR, payload=payload)

        return response


CordClientDataset = EncordClientDataset


class EncordClientProject(EncordClient):
    """
    DEPRECATED - prefer using the :class:`encord.project.Project` instead
    """

    def get_project(self):
        """
        Retrieve project info (pointers to data, labels).

        Returns:
            OrmProject: A project record instance.

        Raises:
            AuthorisationError: If the project API key is invalid.
            ResourceNotFoundError: If no project exists by the specified project EntityId.
            UnknownError: If an error occurs while retrieving the project.
        """
        return self._querier.basic_getter(OrmProject)

    def list_label_rows(
        self,
        edited_before: Optional[Union[str, datetime]] = None,
        edited_after: Optional[Union[str, datetime]] = None,
        label_statuses: Optional[List[AnnotationTaskStatus]] = None,
        shadow_data_state: Optional[ShadowDataState] = None,
        *,
        include_uninitialised_labels=False,
        label_hashes: Optional[List[str]] = None,
        data_hashes: Optional[List[str]] = None,
    ) -> List[LabelRowMetadata]:
        """
        This function is documented in :meth:`encord.project.Project.list_label_rows`.
        """
        if label_statuses:
            label_statuses = [label_status.value for label_status in label_statuses]
        edited_before = parse_datetime("edited_before", edited_before)
        edited_after = parse_datetime("edited_after", edited_after)

        payload = {
            "edited_before": edited_before,
            "edited_after": edited_after,
            "label_statuses": label_statuses,
            "shadow_data_state": shadow_data_state.value if shadow_data_state else None,
            "include_uninitialised_labels": include_uninitialised_labels,
            "data_hashes": data_hashes,
            "label_hashes": label_hashes,
        }
        return self._querier.get_multiple(LabelRowMetadata, payload=payload)

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

        users = self._querier.basic_setter(ProjectUsers, self._config.resource_id, payload=payload)

        return list(map(lambda user: ProjectUser.from_dict(user), users))

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

        return self._querier.basic_setter(ProjectCopy, self._config.resource_id, payload=dataclasses.asdict(payload))

    def get_label_row(
        self,
        uid: str,
        get_signed_url: bool = True,
        *,
        include_object_feature_hashes: Optional[typing.Set[str]] = None,
        include_classification_feature_hashes: Optional[typing.Set[str]] = None,
        include_reviews: bool = False,
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
        }

        return self._querier.basic_getter(LabelRow, uid, payload=payload)

    def get_label_rows(
        self,
        uids: List[str],
        get_signed_url: bool = True,
        *,
        include_object_feature_hashes: Optional[typing.Set[str]] = None,
        include_classification_feature_hashes: Optional[typing.Set[str]] = None,
        include_reviews: bool = False,
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
        }

        return self._querier.get_multiple(LabelRow, uids, payload=payload)

    def save_label_row(self, uid, label):
        """
        This function is documented in :meth:`encord.project.Project.save_label_row`.
        """
        label = LabelRow(label)
        return self._querier.basic_setter(LabelRow, uid, payload=label)

    def create_label_row(self, uid):
        """
        This function is documented in :meth:`encord.project.Project.create_label_row`.
        """
        return self._querier.basic_put(LabelRow, uid=uid, payload=None)

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

    def get_project_ontology(self) -> Ontology:
        project = self.get_project()
        ontology = project["editor_ontology"]
        return Ontology.from_dict(ontology)

    def add_object(self, name: str, shape: ObjectShape) -> bool:
        """
        This function is documented in :meth:`encord.project.Project.add_object`.
        """
        if len(name) == 0:
            raise ValueError("Ontology object name is empty")

        ontology = self.get_project_ontology()
        ontology.add_object(name, shape)
        return self.__set_project_ontology(ontology)

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
        if len(name) == 0:
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

        model = Model(
            {
                "model_operation": ModelOperations.CREATE.value,
                "model_parameters": model_row,
            }
        )

        return self._querier.basic_put(Model, None, payload=model)

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

        if isinstance(device, Device):
            device = device.value

        if device is None or not Device.has_value(device):  # Backward compatibility with string options
            raise encord.exceptions.EncordException(
                message="You must pass a device from the `from encord.constants.model.Device` Enum to run inference."
            )

        inference_params = ModelInferenceParams(
            {
                "files": files,
                "conf_thresh": conf_thresh,
                "iou_thresh": iou_thresh,
                "device": device,
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

    def model_train(
        self,
        uid: str,
        label_rows: Optional[List[str]] = None,
        epochs: Optional[int] = None,
        batch_size: int = 24,
        weights: Optional[ModelTrainingWeights] = None,
        device: Device = Device.CUDA,
    ):
        """
        This function is documented in :meth:`encord.project.Project.model_train`.
        """
        if label_rows is None:
            raise encord.exceptions.EncordException(
                message="You must pass a list of label row uid's (hashes) to train a model."
            )

        if epochs is None:
            raise encord.exceptions.EncordException(message="You must set number of epochs to train a model.")

        if batch_size is None:
            raise encord.exceptions.EncordException(message="You must set a batch size to train a model.")

        if weights is None or not isinstance(weights, ModelTrainingWeights):
            raise encord.exceptions.EncordException(
                message="You must pass weights from the `encord.constants.model_weights` module to train a model."
            )

        if isinstance(device, Device):
            device = device.value

        if device is None or not Device.has_value(device):  # Backward compatibility with string options
            raise encord.exceptions.EncordException(
                message="You must pass a device from the `from encord.constants.model.Device` Enum to train a model."
            )

        training_params = ModelTrainingParams(
            {
                "label_rows": label_rows,
                "epochs": epochs,
                "batch_size": batch_size,
                "weights": weights,
                "device": device,
            }
        )

        model = Model(
            {
                "model_operation": ModelOperations.TRAIN.value,
                "model_parameters": training_params,
            }
        )

        return self._querier.basic_setter(Model, uid, payload=model)

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

    def get_websocket_url(self) -> str:
        return self._config.get_websocket_url()

    def get_label_logs(
        self, user_hash: str = None, data_hash: str = None, from_unix_seconds: int = None, to_unix_seconds: int = None
    ) -> List[LabelLog]:
        """
        This function is documented in :meth:`encord.project.Project.get_label_logs`.
        """

        # Flag for backwards compatibility
        include_user_email_and_interface_key = True

        function_arguments = locals()

        query_payload = {k: v for (k, v) in function_arguments.items() if k != "self" and v is not None}

        return self._querier.get_multiple(LabelLog, payload=query_payload)

    def __set_project_ontology(self, ontology: Ontology) -> bool:
        """
        Save updated project ontology
        Args:
            ontology: the updated project ontology

        Returns:
            bool
        """
        payload = {"editor": ontology.to_dict()}
        return self._querier.basic_setter(OrmProject, uid=None, payload=payload)


CordClientProject = EncordClientProject
