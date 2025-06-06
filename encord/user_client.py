"""---
title: "User Client"
slug: "sdk-ref-user-client"
hidden: false
metadata:
  title: "User Client"
  description: "Encord SDK EncordUserClient classe."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

import base64
import logging
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from enum import Enum
from math import ceil
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union
from uuid import UUID

import requests

import encord.exceptions
from encord.client import EncordClient, EncordClientDataset, EncordClientProject
from encord.client_metadata_schema import get_client_metadata_schema, set_client_metadata_schema_from_dict
from encord.collection import Collection
from encord.common.deprecated import deprecated
from encord.common.time_parser import parse_datetime, parse_datetime_optional
from encord.configs import ENCORD_DOMAIN, BearerConfig, SshConfig, UserConfig, get_env_ssh_key
from encord.constants.string_constants import TYPE_DATASET, TYPE_ONTOLOGY, TYPE_PROJECT
from encord.dataset import Dataset
from encord.filter_preset import FilterPreset
from encord.http.constants import DEFAULT_REQUESTS_SETTINGS, RequestsSettings
from encord.http.querier import Querier
from encord.http.utils import (
    CloudUploadSettings,
    upload_to_signed_url_list,
)
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.metadata_schema import MetadataSchema
from encord.ml_models_client import MlModelsClient
from encord.objects import OntologyStructure
from encord.objects.common import (
    DeidentifyRedactTextMode,
    SaveDeidentifiedDicomCondition,
)
from encord.ontology import Ontology
from encord.orm.client_metadata_schema import ClientMetadataSchemaTypes
from encord.orm.cloud_integration import CloudIntegration, GetCloudIntegrationsParams, GetCloudIntegrationsResponse
from encord.orm.dataset import (
    DEFAULT_DATASET_ACCESS_SETTINGS,
    CreateDatasetPayload,
    CreateDatasetResponse,
    CreateDatasetResponseV2,
    DatasetAccessSettings,
    DatasetInfo,
    DatasetsWithUserRolesListParams,
    DatasetsWithUserRolesListResponse,
    DicomDeidentifyTask,
    Images,
    StorageLocation,
    dataset_user_role_str_enum_to_int_enum,
)
from encord.orm.dataset import Dataset as OrmDataset
from encord.orm.deidentification import (
    DicomDeIdGetResultLongPollingStatus,
    DicomDeIdGetResultParams,
    DicomDeIdGetResultResponse,
    DicomDeIdRedactTextMode,
    DicomDeIdSaveCondition,
    DicomDeIdSaveConditionType,
    DicomDeIdStartPayload,
)
from encord.orm.group import Group as OrmGroup
from encord.orm.ontology import CreateOrUpdateOntologyPayload
from encord.orm.ontology import Ontology as OrmOntology
from encord.orm.project import (
    BenchmarkQaWorkflowSettings,
    CvatExportType,
    CvatImportDataItem,
    CvatImportGetResultLongPollingStatus,
    CvatImportGetResultParams,
    CvatImportGetResultResponse,
    CvatImportStartPayload,
    CvatReviewMode,
    ManualReviewWorkflowSettings,
    ProjectDTO,
    ProjectFilterParams,
    ProjectWorkflowSettings,
    ProjectWorkflowType,
    ReviewMode,
)
from encord.orm.project import Project as OrmProject
from encord.orm.project_with_user_role import ProjectWithUserRole
from encord.orm.storage import CloudSyncedFolderParams, ListFoldersParams, ListItemsParams, StorageItemType
from encord.project import Project
from encord.storage import FoldersSortBy, StorageFolder, StorageItem
from encord.utilities.client_utilities import (
    CvatImporterError,
    CvatImporterSuccess,
    ImportMethod,
    Issues,
    LocalImport,
)
from encord.utilities.ontology_user import OntologiesFilterParams, OntologyUserRole, OntologyWithUserRole
from encord.utilities.project_user import ProjectUserRole

CVAT_LONG_POLLING_RESPONSE_RETRY_N = 3
CVAT_LONG_POLLING_SLEEP_ON_FAILURE_SECONDS = 10
CVAT_LONG_POLLING_MAX_REQUEST_TIME_SECONDS = 60
DICOM_DEID_LONG_POLLING_RESPONSE_RETRY_N = 3
DICOM_DEID_LONG_POLLING_SLEEP_ON_FAILURE_SECONDS = 10
DICOM_DEID_LONG_POLLING_MAX_REQUEST_TIME_SECONDS = 60

log = logging.getLogger(__name__)


class EncordUserClient:
    def __init__(self, config: UserConfig, querier: Querier):
        self._config = config
        self._querier = querier
        self._api_client = ApiClient(config.config)

    @property
    def ml_models(self) -> MlModelsClient:
        """
        Access Encord ML Models functionality.

        Returns:
            MlModelsClient: Client for interacting with Encord's ML models
        """
        return MlModelsClient(self._api_client)

    @property
    def querier(self) -> Querier:
        return self._querier

    @property
    def user_config(self) -> UserConfig:
        return self._config

    def get_bearer_token(self) -> str:
        client = EncordClient(querier=self.querier, config=self._config.config, api_client=self._api_client)
        return client.get_bearer_token().token

    def get_dataset(
        self,
        dataset_hash: Union[str, UUID],
        dataset_access_settings: DatasetAccessSettings = DEFAULT_DATASET_ACCESS_SETTINGS,
    ) -> Dataset:
        """Get the Dataset class to access dataset fields and manipulate a dataset.

        You only have access to this project if you are one of the following

            * Dataset admin

            * Organisation admin of the project

        Args:
            dataset_hash: The Dataset ID
            dataset_access_settings: Set the dataset_access_settings if you would like to change the defaults.
        Returns:
            Returns all Dataset information (title, dataset_hash, dataset_type, and more) and all data rows (including all data row information for each data unit).
        """
        if isinstance(dataset_hash, UUID):
            dataset_hash = str(dataset_hash)

        querier = Querier(self._config.config, resource_type=TYPE_DATASET, resource_id=dataset_hash)
        client = EncordClientDataset(
            querier=querier,
            config=self._config.config,
            dataset_access_settings=dataset_access_settings,
            api_client=self._api_client,
        )
        orm_dataset = client.get_dataset()
        return Dataset(client, orm_dataset)

    def get_project(self, project_hash: Union[str, UUID]) -> Project:
        """Get the Project class to access project fields and manipulate a project.

        You will only have access to this project if you are one of the following

            * Project admin

            * Project team manager

            * Organisation admin of the project

        Args:
            project_hash: The Project ID
        """
        # Querying ontology using project querier to avoid permission error,
        # as there might be only read-only ontology structure access in scope of the project,
        # not full access, that is implied by get_ontology method
        querier = Querier(self._config.config, resource_type=TYPE_PROJECT, resource_id=str(project_hash))
        client = EncordClientProject(querier=querier, config=self._config.config, api_client=self._api_client)
        project_orm = client.get_project_v2()

        project_ontology = self.get_ontology(project_orm.ontology_hash)

        return Project(client, project_orm, project_ontology, self._api_client)

    def get_ontology(self, ontology_hash: str) -> Ontology:
        ontology_with_user_role = self._api_client.get(
            f"ontologies/{ontology_hash}", params=None, result_type=OntologyWithUserRole
        )
        return Ontology._from_api_payload(ontology_with_user_role, self._api_client)

    def __create_dataset(
        self,
        title: str,
        description: Optional[str],
        storage_location: StorageLocation,
        create_backing_folder: bool,
        legacy_call: bool,
    ) -> CreateDatasetResponse:
        res_dataset = self._api_client.post(
            "datasets",
            params=None,
            payload=CreateDatasetPayload(
                title=title,
                description=description,
                create_backing_folder=create_backing_folder,
                legacy_call=legacy_call,
            ),
            result_type=CreateDatasetResponseV2,
            allow_retries=False,
        )

        return CreateDatasetResponse(
            title=title,
            storage_location=storage_location,
            dataset_hash=str(res_dataset.dataset_uuid),
            user_hash="fields withdrawn for compliance reasons",
            backing_folder_uuid=res_dataset.backing_folder_uuid,
        )

    @deprecated("0.1.104", alternative=".create_dataset")
    def create_private_dataset(
        self,
        dataset_title: str,
        dataset_type: StorageLocation,
        dataset_description: Optional[str] = None,
    ) -> CreateDatasetResponse:
        """DEPRECATED - please use `create_dataset` instead."""
        return self.__create_dataset(
            title=dataset_title,
            description=dataset_description,
            storage_location=dataset_type,
            create_backing_folder=True,
            legacy_call=True,
        )

    def create_dataset(
        self,
        dataset_title: str,
        dataset_type: StorageLocation,
        dataset_description: Optional[str] = None,
        create_backing_folder: bool = True,
    ) -> CreateDatasetResponse:
        """
        Args:
            dataset_title (str):
                Title of the dataset.
            dataset_type (StorageLocation):
                Type of storage location where the data will be stored.
            dataset_description (Optional[str]):
                Optional description of the dataset.
            create_backing_folder (bool):
                Whether to create a mirrored backing Folder. If True (default),
                the Folder and Dataset are synced. Recommended to set False for complex
                or large-scale projects.

        Returns:
            CreateDatasetResponse:

        """
        return self.__create_dataset(
            title=dataset_title,
            description=dataset_description,
            storage_location=dataset_type,
            create_backing_folder=create_backing_folder,
            legacy_call=False,
        )

    def get_datasets(
        self,
        title_eq: Optional[str] = None,
        title_like: Optional[str] = None,
        desc_eq: Optional[str] = None,
        desc_like: Optional[str] = None,
        created_before: Optional[Union[str, datetime]] = None,
        created_after: Optional[Union[str, datetime]] = None,
        edited_before: Optional[Union[str, datetime]] = None,
        edited_after: Optional[Union[str, datetime]] = None,
        include_org_access: bool = False,
    ) -> List[Dict[str, Any]]:
        """List either all (if called with no arguments) or matching datasets the user has access to.

        Args:
            title_eq: optional exact title filter
            title_like: optional fuzzy title filter; SQL syntax
            desc_eq: optional exact description filter
            desc_like: optional fuzzy description filter; SQL syntax
            created_before: optional creation date filter, 'less'
            created_after: optional creation date filter, 'greater'
            edited_before: optional last modification date filter, 'less'
            edited_after: optional last modification date filter, 'greater'
            include_org_access: if set to true and the calling user is the organization admin, the
              method returns all datasets in the organization.

        Returns:
            list of datasets matching filter conditions, with the roles that the current user has on them. Each item
            is a dictionary with `"dataset"` and `"user_role"` keys. If include_org_access is set to
            True, some of the datasets may have a `None` value for the `"user_role"` key.
        """
        res = self._api_client.get(
            "/datasets/list",
            params=DatasetsWithUserRolesListParams(
                title_eq=title_eq,
                title_like=title_like,
                description_eq=desc_eq,
                description_like=desc_like,
                created_before=parse_datetime_optional(created_before),
                created_after=parse_datetime_optional(created_after),
                edited_before=parse_datetime_optional(edited_before),
                edited_after=parse_datetime_optional(edited_after),
                include_org_access=include_org_access,
            ),
            result_type=DatasetsWithUserRolesListResponse,
        )

        return [
            {
                "dataset": DatasetInfo(
                    dataset_hash=str(x.dataset_uuid),
                    user_hash="field withdrawn for compliance reasons",
                    title=x.title,
                    description=x.description,
                    type=int(x.storage_location or 0),
                    created_at=x.created_at,
                    last_edited_at=x.last_edited_at,
                    backing_folder_uuid=x.backing_folder_uuid,
                ),
                "user_role": dataset_user_role_str_enum_to_int_enum(x.user_role) if x.user_role is not None else None,
            }
            for x in res.result
        ]

    @staticmethod
    def create_with_ssh_private_key(
        ssh_private_key: Optional[str] = None,
        password: Optional[str] = None,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
        ssh_private_key_path: Optional[Union[str, Path]] = None,
        domain: str = ENCORD_DOMAIN,
        **kwargs,
    ) -> EncordUserClient:
        """Creates an instance of EncordUserClient authenticated with private SSH key.
        Accepts the private key content, path to key file, that can be provided as method parameters or as following environment variables:

        * **ENCORD_SSH_KEY**: environment variable with the private key content
        * **ENCORD_SSH_KEY_FILE**: environment variable with the path to the key file

        Args:
            ssh_private_key: the private key content
            password: private key password
            requests_settings: Request settings. Useful default provided
            ssh_private_key_path: the path to the private key file
            domain: The underlying Encord domain to connect too. Need only be changed for US or Private Clouds
        """
        if ssh_private_key_path is not None:
            if isinstance(ssh_private_key_path, str):
                ssh_private_key_path = Path(ssh_private_key_path)

            ssh_private_key = ssh_private_key_path.read_text(encoding="ascii")

        if not ssh_private_key:
            ssh_private_key = get_env_ssh_key()

        config = SshConfig.from_ssh_private_key(
            ssh_private_key, password, requests_settings=requests_settings, domain=domain, **kwargs
        )
        user_config = UserConfig(config)
        querier = Querier(user_config)
        return EncordUserClient(user_config, querier)

    @staticmethod
    def create_with_bearer_token(
        token: str,
        *,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
        domain: str = ENCORD_DOMAIN,
        **kwargs,
    ) -> EncordUserClient:
        config = BearerConfig.from_bearer_token(
            token=token, requests_settings=requests_settings, domain=domain, **kwargs
        )
        user_config = UserConfig(config)
        querier = Querier(user_config)
        return EncordUserClient(user_config, querier)

    def get_projects(
        self,
        title_eq: Optional[str] = None,
        title_like: Optional[str] = None,
        desc_eq: Optional[str] = None,
        desc_like: Optional[str] = None,
        created_before: Optional[Union[str, datetime]] = None,
        created_after: Optional[Union[str, datetime]] = None,
        edited_before: Optional[Union[str, datetime]] = None,
        edited_after: Optional[Union[str, datetime]] = None,
    ) -> List[Dict]:
        """List either all (if called with no arguments) or matching projects the user has access to.

        Args:
            title_eq: optional exact title filter
            title_like: optional fuzzy title filter; SQL syntax
            desc_eq: optional exact description filter
            desc_like: optional fuzzy description filter; SQL syntax
            created_before: optional creation date filter, 'less'
            created_after: optional creation date filter, 'greater'
            edited_before: optional last modification date filter, 'less'
            edited_after: optional last modification date filter, 'greater'

        Returns:
            list of Projects matching filter conditions, with the roles that the current user has on them. Each item
            is a dictionary with `"project"` and `"user_role"` keys.
        """
        properties_filter = self.__validate_filter(locals())
        # a hack to be able to share validation code without too much c&p
        data = self._querier.get_multiple(ProjectWithUserRole, payload={"filter": properties_filter})
        return [{"project": OrmProject(p.project), "user_role": ProjectUserRole(p.user_role)} for p in data]

    def list_projects(
        self,
        title_eq: Optional[str] = None,
        title_like: Optional[str] = None,
        desc_eq: Optional[str] = None,
        desc_like: Optional[str] = None,
        created_before: Optional[Union[str, datetime]] = None,
        created_after: Optional[Union[str, datetime]] = None,
        edited_before: Optional[Union[str, datetime]] = None,
        edited_after: Optional[Union[str, datetime]] = None,
        include_org_access: bool = False,
    ) -> Iterable[Project]:
        """List either all (if called with no arguments) or matching projects the user has access to.

        Args:
            title_eq: optional exact title filter
            title_like: optional fuzzy title filter; SQL syntax
            desc_eq: optional exact description filter
            desc_like: optional fuzzy description filter; SQL syntax
            created_before: optional creation date filter, 'less'
            created_after: optional creation date filter, 'greater'
            edited_before: optional last modification date filter, 'less'
            edited_after: optional last modification date filter, 'greater'
            include_org_access: if set to true and the calling user is the organization admin, the
              method will return all projects in the organization.

        Returns:
            list of Projects matching filter conditions, as :class:`~encord.project.Project` instances.
        """
        properties_filter = ProjectFilterParams.from_dict(self.__validate_filter(locals()))
        properties_filter.include_org_access = include_org_access
        page = self._api_client.get("projects", params=properties_filter, result_type=Page[ProjectDTO])

        for row in page.results:
            querier = Querier(self._config.config, resource_type=TYPE_PROJECT, resource_id=str(row.project_hash))
            client = EncordClientProject(querier=querier, config=self._config.config, api_client=self._api_client)

            yield Project(
                client=client,
                project_instance=row,
                ontology=None,  # lazy-load
                api_client=self._api_client,
            )

    def create_project(
        self,
        project_title: str,
        dataset_hashes: List[str],
        project_description: str = "",
        ontology_hash: str = "",
        workflow_settings: ProjectWorkflowSettings = ManualReviewWorkflowSettings(),
        workflow_template_hash: Optional[str] = None,
    ) -> str:
        """Creates a new Project and returns its uid ('project_hash')

        Args:
            project_title: the title of the Project
            dataset_hashes: a list of the Dataset uids that the project will use
            project_description: the optional description of the project
            ontology_hash: the uid of an Ontology to be used. If omitted, a new empty Ontology will be created
            workflow_settings: selects and configures the type of the quality control Workflow to use, See :class:`encord.orm.project.ProjectWorkflowSettings` for details. If omitted, :class:`~encord.orm.project.ManualReviewWorkflowSettings` is used.
            workflow_template_hash: Project is created using a Workflow based on the template provided. If omitted, the project will be created using the default standard workflow.

        Returns:
            the uid of the Project.
        """
        project = {
            "title": project_title,
            "description": project_description,
            "dataset_hashes": dataset_hashes,
            "workflow_type": ProjectWorkflowType.MANUAL_QA.value,
        }
        if isinstance(workflow_settings, BenchmarkQaWorkflowSettings):
            project["workflow_type"] = ProjectWorkflowType.BENCHMARK_QA.value
            project["source_projects"] = workflow_settings.source_projects
        if ontology_hash and len(ontology_hash):
            project["ontology_hash"] = ontology_hash

        if workflow_template_hash is not None:
            project["workflow_template_id"] = workflow_template_hash

        return self._querier.basic_setter(OrmProject, uid=None, payload=project)

    @deprecated("0.1.98", ".get_dataset()")
    def get_dataset_client(
        self,
        dataset_hash: str,
        dataset_access_settings: DatasetAccessSettings = DEFAULT_DATASET_ACCESS_SETTINGS,
        **kwargs,
    ) -> EncordClientDataset:
        """DEPRECATED - prefer using :meth:`get_dataset()` instead."""
        if isinstance(dataset_hash, UUID):
            dataset_hash = str(dataset_hash)

        return EncordClientDataset(
            querier=Querier(
                self._config.config,
                resource_type=TYPE_DATASET,
                resource_id=dataset_hash,
            ),
            config=self._config.config,
            dataset_access_settings=dataset_access_settings,
            api_client=self._api_client,
        )

    @deprecated("0.1.98", ".get_project()")
    def get_project_client(
        self,
        project_hash: str,
        **kwargs,
    ) -> EncordClientProject:
        """DEPRECATED - prefer using :meth:`get_project()` instead."""
        if isinstance(project_hash, UUID):
            project_hash = str(project_hash)

        return EncordClientProject(
            querier=Querier(
                self._config.config,
                resource_type=TYPE_PROJECT,
                resource_id=project_hash,
            ),
            config=self._config.config,
            api_client=self._api_client,
        )

    def create_project_from_cvat_start(
        self,
        *,
        import_method: ImportMethod,
        dataset_name: str,
        review_mode: ReviewMode,
        transform_bounding_boxes_to_polygons: bool,
    ) -> UUID:
        """Start importing a CVAT project into Encord. This is the first part of a two-step import process.
        Export your CVAT project with the "CVAT for images 1.1" option and use this function to begin
        importing your images and annotations. Ensure that the "Save images" checkbox is enabled when
        exporting from CVAT.

        Args:
            import_method: The chosen import method. Currently, only LocalImport is supported.
            dataset_name: The name of the dataset that will be created.
            review_mode: Set how much interaction is needed from the labeler and reviewer for the CVAT labels. See the `ReviewMode` documentation for more details.
            transform_bounding_boxes_to_polygons: If True, all instances of CVAT bounding boxes will be converted to polygons in the final Encord project.

        Returns:
            UUID: A unique identifier for tracking the import process.

        Raises:
            ValueError:
                If the CVAT directory has an invalid format or if a non-LocalImport method is used.
        """
        if not isinstance(import_method, LocalImport):
            raise ValueError("Only local imports are currently supported ")

        cvat_directory_path = import_method.file_path

        directory_path = Path(cvat_directory_path)
        images_directory_path = directory_path.joinpath("images")

        if images_directory_path not in list(directory_path.iterdir()):
            raise ValueError("The expected directory 'images' was not found.")

        annotations_file_path = directory_path.joinpath("annotations.xml")

        if not annotations_file_path.is_file():
            raise ValueError(f"The file `{annotations_file_path}` does not exist.")

        with annotations_file_path.open("rb") as f:
            annotations_bytes = f.read()
            annotations_str = annotations_bytes.decode("utf-8")
            annotations_base64 = base64.b64encode(annotations_bytes).decode("utf-8")

        images_paths, used_base_path = self.__get_images_paths(
            annotations_str,
            images_directory_path,
        )

        log.info("Starting image upload.")

        successful_uploads = upload_to_signed_url_list(
            file_paths=images_paths,
            config=self._config,
            api_client=self._api_client,
            upload_item_type=StorageItemType.IMAGE,
            cloud_upload_settings=CloudUploadSettings(),
        )

        if len(images_paths) != len(successful_uploads):
            raise RuntimeError("Could not upload all the images successfully. Aborting CVAT upload.")

        image_title_to_image = {
            str(image_path.relative_to(used_base_path)): {
                "data_hash": successful_upload["data_hash"],
                "file_link": successful_upload["file_link"],
                "title": successful_upload["title"],
            }
            for image_path, successful_upload in zip(
                images_paths,
                successful_uploads,
            )
        }

        log.info("Image upload completed.")

        # This is a bit hacky, but allows more flexibility for CVAT project imports
        if import_method.map_filename_to_cvat_name:
            image_title_to_image = {
                import_method.map_filename_to_cvat_name(key): value for key, value in image_title_to_image.items()
            }

        log.info("Starting project import. This may take a few minutes.")

        dataset_hash = self.create_dataset(
            dataset_name,
            StorageLocation.CORD_STORAGE,
        ).dataset_hash

        cvat_import_uuid = self._api_client.post(
            "projects/cvat-import",
            payload=CvatImportStartPayload(
                annotations_base64=annotations_base64,
                dataset_uuid=UUID(dataset_hash),
                review_mode=CvatReviewMode(review_mode),
                data=[
                    CvatImportDataItem(
                        data_path=data_path,
                        data_link=data["file_link"],
                        title=data["title"],
                    )
                    for data_path, data in image_title_to_image.items()
                ],
                transform_bounding_boxes_to_polygons=transform_bounding_boxes_to_polygons,
            ),
            params=None,
            result_type=UUID,
            allow_retries=False,
        )

        return cvat_import_uuid

    def create_project_from_cvat_get_result(
        self,
        cvat_import_uuid: UUID,
        *,
        timeout_seconds: int = 1 * 24 * 60 * 60,  # 1 day
    ) -> Union[CvatImporterSuccess, CvatImporterError]:
        """Check the status and get the result of a CVAT import process. This is the second part of the
        two-step import process.

        Args:
            cvat_import_uuid: The UUID returned by create_project_from_cvat_start.
            timeout_seconds: Maximum time in seconds to wait for the import to complete. Defaults to 24 hours. The method polls the server periodically during this time.

        Returns:
            Union[CvatImporterSuccess, CvatImporterError]: The result of the import process.
            - CvatImporterSuccess: Contains project_hash, dataset_hash, and any issues if the import succeeded.
            - CvatImporterError: Contains any issues if the import failed.

        Raises:
            ValueError: If the server returns an unexpected status or invalid response structure.
        """
        failed_requests_count = 0
        polling_start_timestamp = time.perf_counter()

        while True:
            try:
                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                log.info(f"create_project_from_cvat_get_result started polling call {polling_elapsed_seconds=}")
                tmp_res = self._api_client.get(
                    f"projects/cvat-import/{cvat_import_uuid}",
                    params=CvatImportGetResultParams(
                        timeout_seconds=min(
                            polling_available_seconds,
                            CVAT_LONG_POLLING_MAX_REQUEST_TIME_SECONDS,
                        ),
                    ),
                    result_type=CvatImportGetResultResponse,
                )

                if tmp_res.status == CvatImportGetResultLongPollingStatus.DONE:
                    log.info(f"cvat import job completed with cvat_import_uuid={cvat_import_uuid}.")

                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                if polling_available_seconds == 0 or tmp_res.status in [
                    CvatImportGetResultLongPollingStatus.DONE,
                    CvatImportGetResultLongPollingStatus.ERROR,
                ]:
                    res = tmp_res
                    break

                failed_requests_count = 0
            except (requests.exceptions.RequestException, encord.exceptions.RequestException):
                failed_requests_count += 1

                if failed_requests_count >= CVAT_LONG_POLLING_RESPONSE_RETRY_N:
                    raise

                time.sleep(CVAT_LONG_POLLING_SLEEP_ON_FAILURE_SECONDS)

        if res.status == CvatImportGetResultLongPollingStatus.DONE:
            if res.project_uuid is None:
                raise ValueError(f"{res.project_uuid=}, res.project_uuid should not be None with DONE status")

            if res.issues is None:
                raise ValueError(f"{res.issues=}, res.issues should not be None with DONE status")

            return CvatImporterSuccess(
                project_hash=str(res.project_uuid),
                dataset_hash=str(list(self.get_project(res.project_uuid).list_datasets())[0]),
                issues=Issues.from_dict(res.issues),
            )
        elif res.status == CvatImportGetResultLongPollingStatus.ERROR:
            if res.issues is None:
                raise ValueError(f"{res.issues=}, res.issues should not be None with DONE status")

            return CvatImporterError(
                issues=Issues.from_dict(res.issues),
            )
        else:
            raise ValueError(f"{res.status=}, only DONE and ERROR status is expected after successful long polling")

    def create_project_from_cvat(
        self,
        import_method: ImportMethod,
        dataset_name: str,
        review_mode: ReviewMode = ReviewMode.LABELLED,
        *,
        transform_bounding_boxes_to_polygons=False,
        timeout_seconds: int = 1 * 24 * 60 * 60,  # 1 day
    ) -> Union[CvatImporterSuccess, CvatImporterError]:
        """Create a new Encord project from a CVAT export. This method combines the two-step import process
        (create_project_from_cvat_start and create_project_from_cvat_get_result) into a single call.
        Export your CVAT project with the "CVAT for images 1.1" option and use this function to import
        your images and annotations. Ensure that the "Save images" checkbox is enabled when exporting
        from CVAT.

        Args:
            import_method: The chosen import method. Currently, only LocalImport is supported.
            dataset_name: The name of the dataset that will be created.
            review_mode: Set how much interaction is needed from the labeler and reviewer for the CVAT labels. See the `ReviewMode` documentation for more details. Defaults to ReviewMode.LABELLED.
            transform_bounding_boxes_to_polygons: If True, all instances of CVAT bounding boxes will be converted to polygons in the final Encord project. Defaults to False.
            timeout_seconds: Maximum time in seconds to wait for the import to complete. Defaults to 24 hours. The method polls the server periodically during this time.

        Returns:
            Union[CvatImporterSuccess, CvatImporterError]: The result of the import process.
            - CvatImporterSuccess: Contains project_hash, dataset_hash, and any issues if the import succeeded.
            - CvatImporterError: Contains any issues if the import failed.

        Raises:
            ValueError:If the CVAT directory has an invalid format, if a non-LocalImport method is used, or if the server returns an unexpected status.
        """
        return self.create_project_from_cvat_get_result(
            cvat_import_uuid=self.create_project_from_cvat_start(
                import_method=import_method,
                dataset_name=dataset_name,
                review_mode=review_mode,
                transform_bounding_boxes_to_polygons=transform_bounding_boxes_to_polygons,
            ),
            timeout_seconds=timeout_seconds,
        )

    def __get_images_paths(
        self,
        annotations_str: str,
        images_directory_path: Path,
    ) -> Tuple[List[Path], Path]:
        meta_tags = [x.tag for x in ET.fromstring(annotations_str).find("meta") or []]

        if CvatExportType.PROJECT.value in meta_tags:
            default_path = images_directory_path.joinpath("default")

            if default_path not in list(images_directory_path.iterdir()):
                raise ValueError("The expected directory 'default' was not found.")

            used_base_path = default_path
            # NOTE: it is possible that here we also need to use the __get_recursive_image_paths
            images = list(default_path.iterdir())

        elif CvatExportType.TASK.value in meta_tags:
            used_base_path = images_directory_path
            images = self.__get_recursive_image_paths(images_directory_path)

        else:
            raise ValueError(
                "Neither the 'project' nor the 'task' field was found in the CVAT annotations' 'meta' "
                "field. The annotation file is likely ill-formed."
            )

        if not images:
            raise ValueError("No images found in the provided data folder.")

        return images, used_base_path

    @staticmethod
    def __get_recursive_image_paths(images_directory_path: Path) -> List[Path]:
        """Recursively get all the images in all the sub folders."""
        return [file for file in images_directory_path.glob("**/*") if file.is_file()]

    def get_cloud_integrations(
        self,
        filter_integration_uuids: Optional[Union[List[UUID], List[str], List[Union[UUID, str]]]] = None,
        filter_integration_titles: Optional[List[str]] = None,
        include_org_access: bool = False,
    ) -> List[CloudIntegration]:
        """List either all (if called with no arguments) or matching cloud integrations the user has access to.

        Args:
            filter_integration_uuids: optional list of integration UUIDs to include.
            filter_integration_titles: optional list of integration titles to include (exact match).
            include_org_access: if set to true and the calling user is the organization admin, the
              method will return all cloud integrations in the organization.

        If `filter_integration_uuids` and `filter_integration_titles` are both provided, the method will return
        the integrations that match both of the filters.
        """
        if filter_integration_uuids is not None:
            filter_integration_uuids = [UUID(x) if isinstance(x, str) else x for x in filter_integration_uuids]
        return [
            CloudIntegration(
                id=str(x.integration_uuid),
                title=x.title,
            )
            for x in self._api_client.get(
                "cloud-integrations",
                params=GetCloudIntegrationsParams(
                    filter_integration_uuids=filter_integration_uuids,
                    filter_integration_titles=filter_integration_titles,
                    include_org_access=include_org_access,
                ),
                result_type=GetCloudIntegrationsResponse,
            ).result
        ]

    def get_ontologies(
        self,
        title_eq: Optional[str] = None,
        title_like: Optional[str] = None,
        desc_eq: Optional[str] = None,
        desc_like: Optional[str] = None,
        created_before: Optional[Union[str, datetime]] = None,
        created_after: Optional[Union[str, datetime]] = None,
        edited_before: Optional[Union[str, datetime]] = None,
        edited_after: Optional[Union[str, datetime]] = None,
        include_org_access: bool = False,
    ) -> List[Dict]:
        """List either all (if called with no arguments) or matching ontologies the user has access to.

        Args:
            title_eq: optional exact title filter
            title_like: optional fuzzy title filter; SQL syntax
            desc_eq: optional exact description filter
            desc_like: optional fuzzy description filter; SQL syntax
            created_before: optional creation date filter, 'less'
            created_after: optional creation date filter, 'greater'
            edited_before: optional last modification date filter, 'less'
            edited_after: optional last modification date filter, 'greater'
            include_org_access: if set to true and the calling user is the organization admin, the
              method will return all ontologies in the organization.

        Returns:
            list of ontologies matching filter conditions, with the roles that the current user has on them. Each item
            is a dictionary with `"ontology"` and `"user_role"` keys. If include_org_access is set to
            True, some of the ontologies may have a `None` value for the `"user_role"` key.
        """
        properties_filter = OntologiesFilterParams.from_dict(self.__validate_filter(locals()))
        properties_filter.include_org_access = include_org_access
        page = self._api_client.get("ontologies", params=properties_filter, result_type=Page[OntologyWithUserRole])

        # a hack to be able to share validation code without too much c&p
        retval: List[Dict] = []
        for row in page.results:
            retval.append(
                {
                    "ontology": Ontology._from_api_payload(row, self._api_client),
                    "user_role": row.user_role,
                }
            )
        return retval

    def create_ontology(
        self,
        title: str,
        description: str = "",
        structure: Optional[OntologyStructure] = None,
    ) -> Ontology:
        """Creates a new ontology with the given title, description, and structure.

        Args:
        title (str): The title of the ontology.
        description (str, optional): A brief description of the ontology. Defaults to an empty string.
        structure (Optional[OntologyStructure], optional): The structural definition of the ontology. If not provided, a default structure is used.

        Returns:
        Ontology: The newly created ontology object.

        Raises:
        ValueError: If the provided structure contains a classification without any attributes.
        """
        try:
            structure_dict = structure.to_dict() if structure else OntologyStructure().to_dict()
        except ValueError as e:
            raise ValueError("Can't create an Ontology containing a Classification without any attributes. " + str(e))

        payload = CreateOrUpdateOntologyPayload(
            title=title,
            description=description,
            editor=structure_dict,
        )

        ontology = self._api_client.post(
            "ontologies",
            payload=payload,
            params=None,
            result_type=OntologyWithUserRole,
            allow_retries=False,
        )

        return Ontology._from_api_payload(ontology, self._api_client)

    def __validate_filter(self, properties_filter: Dict) -> Dict:
        if not isinstance(properties_filter, dict):
            raise ValueError("Filter should be a dictionary")

        valid_filters = set([f.value for f in ListingFilter])

        ret = dict()

        # be relaxed with what we receive: translate raw strings to enum values
        for clause, val in properties_filter.items():
            if val is None:
                continue

            if isinstance(clause, str):
                if clause in valid_filters:
                    clause = ListingFilter(clause)
                else:
                    continue
            elif not isinstance(clause, ListingFilter):
                continue

            if clause.value.endswith("before") or clause.value.endswith("after"):
                if isinstance(val, str):
                    val = parse_datetime(val)
                if isinstance(val, datetime):
                    val = val.isoformat()
                else:
                    raise ValueError(f"Value for {clause.name} filter should be a datetime")

            ret[clause.value] = val

        return ret

    def list_groups(self) -> Iterable[OrmGroup]:
        """List all groups belonging to the user's current organization."""
        page = self._api_client.get("user/current-organisation/groups", params=None, result_type=Page[OrmGroup])
        yield from page.results

    def deidentify_dicom_files_start(
        self,
        dicom_urls: List[str],
        integration_hash: str,
        redact_dicom_tags: bool = True,
        redact_pixels_mode: DeidentifyRedactTextMode = DeidentifyRedactTextMode.REDACT_NO_TEXT,
        save_conditions: Optional[List[SaveDeidentifiedDicomCondition]] = None,
        upload_dir: Optional[str] = None,
    ) -> UUID:
        """Initiate the DICOM files deidentification process.

        This method starts the deidentification job for the specified DICOM files and returns
        a UUID that can be used to track and retrieve the deidentification job results.

        Args:
            dicom_urls: A list of URLs pointing to DICOM files to be deidentified.
            integration_hash: Integration hash for the external storage integration.
            redact_dicom_tags: Flag to enable or disable DICOM tags redaction. Defaults to True.
            redact_pixels_mode: Policy for redacting text in pixel data.
                Defaults to DeidentifyRedactTextMode.REDACT_NO_TEXT.
            save_conditions: Optional list of conditions that must be met for
                a deidentified DICOM file to be saved.
            upload_dir: Optional directory for uploading deidentified files.
                If None, files will be uploaded to the same directory as source files.

        Returns:
            A UUID representing the initiated deidentification job,
            which can be used to retrieve job results.
        """
        if save_conditions is None:
            save_conditions_api = None
        else:
            save_conditions_api = [
                DicomDeIdSaveCondition(
                    value=x.value,
                    condition_type=DicomDeIdSaveConditionType[x.condition_type.value],
                    dicom_tag=x.dicom_tag,
                )
                for x in save_conditions
            ]

        dicom_deid_uuid = self._api_client.post(
            "dicom-deidentification",
            payload=DicomDeIdStartPayload(
                integration_uuid=uuid.UUID(integration_hash),
                dicom_urls=dicom_urls,
                redact_dicom_tags=redact_dicom_tags,
                redact_pixels_mode=DicomDeIdRedactTextMode[redact_pixels_mode.name],
                save_conditions=save_conditions_api,
                upload_dir=upload_dir,
            ),
            params=None,
            result_type=UUID,
            allow_retries=False,
        )

        return dicom_deid_uuid

    def deidentify_dicom_files_get_result(
        self,
        dicom_deid_uuid: UUID,
        *,
        timeout_seconds: int = 1 * 24 * 60 * 60,  # 1 day
    ) -> List[str]:
        """Retrieve the results of a DICOM deidentification job.

        This method polls the server to check the status of a previously initiated
        DICOM deidentification job and returns the URLs of deidentified files
        when the job is complete.

        Args:
            dicom_deid_uuid: The UUID of the deidentification job returned by deidentify_dicom_files_start(...).
            timeout_seconds: Maximum time to wait for job completion. Defaults to 1 day (86400 seconds).

        Returns:
            A list of URLs pointing to the deidentified DICOM files.
        """
        failed_requests_count = 0
        polling_start_timestamp = time.perf_counter()

        while True:
            try:
                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                log.info(f"deidentify_dicom_files_get_result started polling call {polling_elapsed_seconds=}")
                tmp_res = self._api_client.get(
                    f"dicom-deidentification/{dicom_deid_uuid}",
                    params=DicomDeIdGetResultParams(
                        timeout_seconds=min(
                            polling_available_seconds,
                            DICOM_DEID_LONG_POLLING_MAX_REQUEST_TIME_SECONDS,
                        ),
                    ),
                    result_type=DicomDeIdGetResultResponse,
                )

                if tmp_res.status == DicomDeIdGetResultLongPollingStatus.DONE:
                    log.info(f"dicom deidentification job completed with {dicom_deid_uuid=}.")

                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                if polling_available_seconds == 0 or tmp_res.status in [
                    DicomDeIdGetResultLongPollingStatus.DONE,
                    DicomDeIdGetResultLongPollingStatus.ERROR,
                ]:
                    res = tmp_res
                    break

                failed_requests_count = 0
            except (requests.exceptions.RequestException, encord.exceptions.RequestException):
                failed_requests_count += 1

                if failed_requests_count >= DICOM_DEID_LONG_POLLING_RESPONSE_RETRY_N:
                    raise

                time.sleep(DICOM_DEID_LONG_POLLING_SLEEP_ON_FAILURE_SECONDS)

        if res.status == DicomDeIdGetResultLongPollingStatus.DONE:
            if res.urls is None:
                raise ValueError(f"{type(res.urls)=}, res.urls should not be None with DONE status")

            return res.urls
        elif res.status == DicomDeIdGetResultLongPollingStatus.ERROR:
            raise ValueError(f"dicom deidentification job failed, {dicom_deid_uuid=}, please contact support")
        else:
            raise ValueError(f"{res.status=}, only DONE and ERROR status is expected after successful long polling")

    def deidentify_dicom_files(
        self,
        dicom_urls: List[str],
        integration_hash: str,
        redact_dicom_tags: bool = True,
        redact_pixels_mode: DeidentifyRedactTextMode = DeidentifyRedactTextMode.REDACT_NO_TEXT,
        save_conditions: Optional[List[SaveDeidentifiedDicomCondition]] = None,
        upload_dir: Optional[str] = None,
    ) -> List[str]:
        """Deidentify DICOM files in external storage.
        Given links to DICOM files pointing to AWS, GCP, AZURE or OTC, for example:
        [ "https://s3.region-code.amazonaws.com/bucket-name/dicom-file-input.dcm" ]
        Function executes deidentification on those files, it removes all
        DICOM tags (https://dicom.nema.org/medical/Dicom/2017e/output/chtml/part06/chapter_6.html)
        from metadata except for:

        * x00080018 SOPInstanceUID
        * x00100010 PatientName
        * x00180050 SliceThickness
        * x00180088 SpacingBetweenSlices
        * x0020000d StudyInstanceUID
        * x0020000e SeriesInstanceUID
        * x00200032 ImagePositionPatient
        * x00200037 ImageOrientationPatient
        * x00280008 NumberOfFrames
        * x00281050 WindowCenter
        * x00281051 WindowWidth
        * x00520014 ALinePixelSpacing

        Args:
            self: Encord client object.
            dicom_urls: a list of urls to DICOM files, for example: `[ "https://s3.region-code.amazonaws.com/bucket-name/dicom-file-input.dcm" ]`
            integration_hash: integration_hash parameter of Encord platform external storage integration
            redact_dicom_tags: Specifies if DICOM tags redaction should be enabled.
            redact_pixels_mode: Specifies which text redaction policy should be applied to pixel data.
            save_conditions: Specifies a list of conditions which all have to be true for DICOM deidentified file to be saved.
            upload_dir: Specifies a directory that files will be uploaded to. By default, set to None, deidentified files will be uploaded to the same directory as source files.

        Returns:
            Function returns list of links pointing to deidentified DICOM files,
            those will be saved to the same bucket and the same directory
            as original files with prefix ( deid_{timestamp}_ ).
            Example output:
            `[ "https://s3.region-code.amazonaws.com/bucket-name/deid_167294769118005312_dicom-file-input.dcm" ]`

        """
        return self.deidentify_dicom_files_get_result(
            dicom_deid_uuid=self.deidentify_dicom_files_start(
                dicom_urls=dicom_urls,
                integration_hash=integration_hash,
                redact_dicom_tags=redact_dicom_tags,
                redact_pixels_mode=redact_pixels_mode,
                save_conditions=save_conditions,
                upload_dir=upload_dir,
            )
        )

    def create_storage_folder(
        self,
        name: str,
        description: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        parent_folder: Optional[Union[StorageFolder, UUID]] = None,
        cloud_synced_folder_params: Optional[CloudSyncedFolderParams] = None,
    ) -> StorageFolder:
        """Create a new storage folder.

        Args:
            name: The name of the folder.
            description: The description of the folder.
            client_metadata: Optional arbitrary metadata to be associated with the folder. Should be a dictionary
                that is JSON-serializable.
            parent_folder: The parent folder of the folder; or `None` if the folder is to be created at the root level.
            cloud_synced_folder_params: Passing this will create cloud synced folder, leaving this a `None` will create
                a normal folder for further data uploads.

        Returns:
            The created storage folder. See :class:`encord.storage.StorageFolder` for details.
        """
        return StorageFolder._create_folder(
            api_client=self._api_client,
            name=name,
            description=description,
            client_metadata=client_metadata,
            parent_folder=parent_folder,
            cloud_synced_folder_params=cloud_synced_folder_params,
        )

    def get_storage_folder(self, folder_uuid: Union[UUID, str]) -> StorageFolder:
        """Get a storage folder by its UUID.

        Args:
            folder_uuid: The UUID of the folder to retrieve.

        Returns:
            The storage folder. See :class:`encord.storage.StorageFolder` for details.

        Raises:
            ValueError: If `folder_uuid` is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the folder with the given UUID does not exist or
                the user does not have access to it.
        """
        if isinstance(folder_uuid, str):
            folder_uuid = UUID(folder_uuid)
        return StorageFolder._get_folder(self._api_client, folder_uuid)

    def get_storage_item(self, item_uuid: Union[UUID, str], sign_url: bool = False) -> StorageItem:
        """Get a storage item by its unique identifier.

        Args:
            item_uuid: The UUID of the item to retrieve.
            sign_url: If `True`, pre-fetch a signed URL for the item (otherwise the URL will be signed on demand).

        Returns:
            The storage item. See :class:`encord.storage.StorageItem` for details.

        Raises:
            ValueError: If `item_uuid` is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the item with the given UUID does not exist or
                the user does not have access to it.
        """
        if isinstance(item_uuid, str):
            item_uuid = UUID(item_uuid)
        return StorageItem._get_item(self._api_client, item_uuid, sign_url)

    def get_storage_items(
        self,
        item_uuids: Sequence[Union[UUID, str]],
        sign_url: bool = False,
    ) -> List[StorageItem]:
        """Get storage items by their UUIDs, in bulk. Useful for retrieving multiple items at once, e.g. when getting
        items pointed to by :attr:`encord.orm.dataset.DataRow.backing_item_uuid` for all data rows of a dataset.

        Args:
            item_uuids: list of UUIDs of items to retrieve. Can be a list of strings or a list of UUID objects.
            sign_url: If `True`, pre-fetch a signed URLs for the items (otherwise the URLs will be signed on demand).

        Returns:
            A list of storage items. See :class:`encord.storage.StorageItem` for details. Items will be in the same order as `item_uuids` in the request

        Raises:
            ValueError: If any of the item uuids is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If some of the items with the given UUIDs do not exist or
                the user does not have access to them.
        """
        internal_item_uuids: List[UUID] = [UUID(item) if isinstance(item, str) else item for item in item_uuids]
        return StorageItem._get_items(self._api_client, internal_item_uuids, sign_url)

    def list_storage_folders(
        self,
        *,
        search: Optional[str] = None,
        dataset_synced: Optional[bool] = None,
        org_access: Optional[bool] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable[StorageFolder]:
        """List top-level storage folders.

        Args:
            search: Search string to filter folders by name (optional)
            dataset_synced: Include or exclude folders that are mirrored by a dataset. Optional; if `None`,
                no filtering is applied.
            org_access: If `True`, and if the caller is `ADMIN` of their organization, the results contain the
                folders belonging to the organization, instead of those accessible to the user. If enabled
                but the user is not an organization admin, the `AuthorisationError` is raised. Default value is `False`.
            order: Sort order for the folders. See :class:`encord.storage.FoldersSortBy` for available options.
            desc: If True, sort in descending order.
            page_size: Number of folders to return per page. Default if not specified is 100. Maximum value is 1000.

        Returns:
            Iterable of :class:`encord.StorageFolder` objects.
        """
        return StorageFolder._list_folders(
            self._api_client,
            "storage/folders",
            ListFoldersParams(
                search=search,
                dataset_synced=dataset_synced,
                include_org_access=org_access,
                order=order,
                desc=desc,
                page_size=page_size,
            ),
        )

    def find_storage_folders(
        self,
        *,
        search: Optional[str] = None,
        dataset_synced: Optional[bool] = None,
        org_access: Optional[bool] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        page_size: int = 100,
    ) -> Iterable[StorageFolder]:
        """Recursively search for storage folders, starting from the top level.

        Args:
            search: Search string to filter folders by name (optional)
            dataset_synced: Include or exclude folders that are mirrored by a dataset. Optional; if `None`,
                no filtering is applied.
            org_access: If `True`, and if the caller is `ADMIN` of their organization, the results contain the
                folders belonging to the organization, instead of those accessible to the user. If enabled
               but the user is not an organization admin, the `AuthorisationError` is raised. Default value is `False`.
            order: Sort order for the folders. See :class:`encord.storage.FoldersSortBy` for available options.
            desc: If True, sort in descending order.
            page_size: Number of folders to return per page. Default if not specified is 100. Maximum value is 1000.

        Returns:
            Iterable of :class:`encord.StorageFolder` objects.
        """
        return StorageFolder._list_folders(
            self._api_client,
            "storage/search/folders",
            ListFoldersParams(
                search=search,
                dataset_synced=dataset_synced,
                include_org_access=org_access,
                order=order,
                desc=desc,
                page_size=page_size,
            ),
        )

    def find_storage_items(
        self,
        *,
        search: Optional[str] = None,
        is_in_dataset: Optional[bool] = None,
        item_types: Optional[List[StorageItemType]] = None,
        org_access: Optional[bool] = None,
        order: FoldersSortBy = FoldersSortBy.NAME,
        desc: bool = False,
        get_signed_urls: bool = False,
        page_size: int = 100,
    ) -> Iterable[StorageItem]:
        """Recursively search for storage items, starting from the root level.

        Warning: This method is slow. We recommend using `storage_folder.list_items` instead.

        Args:
            search: Search string to filter items by name.
            is_in_dataset: Filter items by whether they are linked to any dataset. `True` and `False` select
                only linked and only unlinked items, respectively. `None` includes all items regardless of their
                dataset links.
            item_types: Filter items by type.
            org_access: If `True`, and if the caller is `ADMIN` of their organization, the results contain the
               items belonging to the organization, instead of those accessible to the user. If enabled
                but the user is not an organization admin, the `AuthorisationError` is raised. Default value is `False`.
            order: Sort order.
            desc: Sort in descending order.
            get_signed_urls: If True, return signed URLs for the items.
            page_size: Number of items to return per page. Default if not specified is 100. Maximum value is 1000.

        At least one of `search` or `item_types` must be provided.

        Returns:
            Iterable of items in the folder.
        """
        params = ListItemsParams(
            search=search,
            is_in_dataset=is_in_dataset,
            item_types=item_types or [],
            include_org_access=org_access,
            order=order,
            desc=desc,
            page_token=None,
            page_size=page_size,
            sign_urls=get_signed_urls,
        )

        return StorageFolder._list_items(self._api_client, "storage/search/items", params)

    @deprecated("0.1.132", ".metadata_schema()")
    def get_client_metadata_schema(self) -> Optional[Dict[str, ClientMetadataSchemaTypes]]:
        return get_client_metadata_schema(self._api_client)

    @deprecated("0.1.132", ".metadata_schema()")
    def set_client_metadata_schema_from_dict(self, json_dict: Dict[str, ClientMetadataSchemaTypes]):
        set_client_metadata_schema_from_dict(self._api_client, json_dict)

    def metadata_schema(self) -> MetadataSchema:
        return MetadataSchema(self._api_client)

    def get_collection(self, collection_uuid: Union[str, UUID]) -> Collection:
        """Get a collection by its unique identifier (UUID).

        Args:
            collection_uuid: The unique identifier of the collection to retrieve.

        Returns:
            The collection. See :class:`encord.collection.Collection` for details.

        Raises:
            ValueError: If `collection_uuid` is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the item with the given UUID does not exist or
                the user does not have access to it.
        """
        if isinstance(collection_uuid, str):
            collection_uuid = UUID(collection_uuid)

        return Collection._get_collection(self._api_client, collection_uuid=collection_uuid)

    def list_collections(
        self,
        top_level_folder_uuid: Union[str, UUID, None] = None,
        collection_uuids: Optional[List[Union[str, UUID]]] = None,
        page_size: Optional[int] = None,
    ) -> Iterator[Collection]:
        """Get collections by top level folder or list of collection IDs.
        If both top_level_folder_uuid and collection_uuid_list are preset
        then the intersection of the two conditions is returned.

        Args:
            top_level_folder_uuid: The unique identifier of the top level folder.
            collection_uuids: The unique identifiers (UUIDs) of the collections to retrieve.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            The list of collections which match the given criteria.

        Raises:
            ValueError: If `top_level_folder_uuid` or any of the collection uuids is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        if isinstance(top_level_folder_uuid, str):
            top_level_folder_uuid = UUID(top_level_folder_uuid)
        collections = (
            [UUID(collection) if isinstance(collection, str) else collection for collection in collection_uuids]
            if collection_uuids is not None
            else None
        )
        return Collection._list_collections(
            self._api_client,
            top_level_folder_uuid=top_level_folder_uuid,
            collection_uuids=collections,
            page_size=page_size,
        )

    def delete_collection(self, collection_uuid: Union[str, UUID]) -> None:
        """Delete a collection by its UUID if it exists.

        Args:
            collection_uuid: The unique identifier (UUID) of the collection to delete.

        Returns:
            None

        Raises:
            ValueError: If `collection_uuid` is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        if isinstance(collection_uuid, str):
            collection_uuid = UUID(collection_uuid)
        Collection._delete_collection(self._api_client, collection_uuid)

    def create_collection(
        self, top_level_folder_uuid: Union[str, UUID], name: str, description: str = ""
    ) -> Collection:
        """Create a collection.

        Args:
            top_level_folder_uuid: The unique identifier (UUID) of the folder that the collection is created in.
            name: The name of the collection.
            description: The description of the collection.

        Returns:
            Collection: Newly created collection.

        Raises:
            ValueError: If `top_level_folder_uuid` is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to the folder.
        """
        if isinstance(top_level_folder_uuid, str):
            top_level_folder_uuid = UUID(top_level_folder_uuid)
        new_uuid = Collection._create_collection(self._api_client, top_level_folder_uuid, name, description)
        return self.get_collection(new_uuid)

    def get_filter_preset(self, preset_uuid: Union[str, UUID]) -> FilterPreset:
        """Get a preset by its unique identifier (UUID).

        Args:
            preset_uuid: The unique identifier of the preset to retrieve.

        Returns:
            The preset. See :class:`encord.preset.Preset` for details.

        Raises:
            ValueError: If `preset_uuid` is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the item with the given UUID does not exist or
                the user does not have access to it.
        """
        if isinstance(preset_uuid, str):
            preset_uuid = UUID(preset_uuid)
        return FilterPreset._get_preset(self._api_client, preset_uuid=preset_uuid)

    def get_filter_presets(
        self, preset_uuids: List[Union[str, UUID]] = [], page_size: Optional[int] = None
    ) -> Iterator[FilterPreset]:
        """Get presets by list of preset unique identifiers (UUIDs).

        Args:
            preset_uuids: The list of unique identifiers (UUIDs) to be retrieved.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            The list of presets which match the given criteria.

        Raises:
            ValueError: If any of the preset uuids is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        internal_preset_uuids: List[UUID] = [
            UUID(collection) if isinstance(collection, str) else collection for collection in preset_uuids
        ]
        return FilterPreset._get_presets(self._api_client, internal_preset_uuids, page_size=page_size)

    def list_presets(
        self, top_level_folder_uuid: Union[str, UUID, None] = None, page_size: Optional[int] = None
    ) -> Iterator[FilterPreset]:
        """Get presets by top level folder.

        Args:
            top_level_folder_uuid: The unique identifier of the top level folder.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            The list of presets which match the given criteria.

        Raises:
            ValueError: If `top_level_folder_uuid` is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        if isinstance(top_level_folder_uuid, str):
            top_level_folder_uuid = UUID(top_level_folder_uuid)
        return FilterPreset._list_presets(self._api_client, top_level_folder_uuid, page_size=page_size)

    def create_preset(self, name: str, filter_preset_json: dict, description: str = "") -> FilterPreset:
        """Create a preset.

        Args:
            name: The name of the preset.
            description: The description of the preset.
            filter_preset_json: The filters for the preset in their raw json format.

        Returns:
            FilterPreset: Newly created collection.
        """
        new_uuid = FilterPreset._create_preset(
            self._api_client, name, description=description, filter_preset_json=filter_preset_json
        )
        return self.get_filter_preset(new_uuid)

    def delete_preset(self, preset_uuid: Union[str, UUID]) -> None:
        """Delete a preset by its unique identifier (UUID) if it exists.

        Args:
            preset_uuid: The uuid/id of the preset to delete.

        Returns:
            None

        Raises:
            ValueError: If `preset_uuid` is a badly formed UUID.
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        if isinstance(preset_uuid, str):
            preset_uuid = UUID(preset_uuid)
        FilterPreset._delete_preset(self._api_client, preset_uuid)


class ListingFilter(Enum):
    """Available properties_filter keys for get_projects() and get_datasets().

    The values for *_before* and *_after* should be datetime objects.
    """

    TITLE_EQ = "title_eq"
    TITLE_LIKE = "title_like"
    DESC_EQ = "desc_eq"
    DESC_LIKE = "desc_like"
    CREATED_BEFORE = "created_before"
    CREATED_AFTER = "created_after"
    EDITED_BEFORE = "edited_before"
    EDITED_AFTER = "edited_after"
