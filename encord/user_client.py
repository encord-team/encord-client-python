"""
---
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
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union
from uuid import UUID

from encord.client import EncordClient, EncordClientDataset, EncordClientProject
from encord.client_metadata_schema import get_client_metadata_schema, set_client_metadata_schema_from_dict
from encord.collection import Collection
from encord.common.deprecated import deprecated
from encord.common.time_parser import parse_datetime
from encord.configs import BearerConfig, SshConfig, UserConfig, get_env_ssh_key
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
from encord.objects import OntologyStructure
from encord.objects.common import (
    DeidentifyRedactTextMode,
    SaveDeidentifiedDicomCondition,
)
from encord.ontology import Ontology
from encord.orm.client_metadata_schema import ClientMetadataSchemaTypes
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import (
    DEFAULT_DATASET_ACCESS_SETTINGS,
    CreateDatasetResponse,
    DatasetAccessSettings,
    DatasetAPIKey,
    DatasetInfo,
    DatasetScope,
    DatasetUserRole,
    DicomDeidentifyTask,
    Images,
    StorageLocation,
)
from encord.orm.dataset import Dataset as OrmDataset
from encord.orm.dataset_with_user_role import DatasetWithUserRole
from encord.orm.group import Group as OrmGroup
from encord.orm.ontology import Ontology as OrmOntology
from encord.orm.project import (
    BenchmarkQaWorkflowSettings,
    CvatExportType,
    ManualReviewWorkflowSettings,
    ProjectImporter,
    ProjectImporterCvatInfo,
    ProjectWorkflowSettings,
    ProjectWorkflowType,
    ReviewMode,
)
from encord.orm.project import Project as OrmProject
from encord.orm.project_api_key import ProjectAPIKey
from encord.orm.project_with_user_role import ProjectWithUserRole
from encord.orm.storage import CreateStorageFolderPayload, ListFoldersParams, ListItemsParams, StorageItemType
from encord.orm.storage import StorageFolder as OrmStorageFolder
from encord.project import Project
from encord.storage import FoldersSortBy, StorageFolder, StorageItem
from encord.utilities.client_utilities import (
    APIKeyScopes,
    CvatImporterError,
    CvatImporterSuccess,
    ImportMethod,
    Issues,
    LocalImport,
)
from encord.utilities.ontology_user import OntologyUserRole, OntologyWithUserRole
from encord.utilities.project_user import ProjectUserRole

log = logging.getLogger(__name__)


class EncordUserClient:
    def __init__(self, config: UserConfig, querier: Querier):
        self._config = config
        self._querier = querier
        self._api_client = ApiClient(config.config)

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
        """
        Get the Dataset class to access dataset fields and manipulate a dataset.

        You only have access to this project if you are one of the following

            * Dataset admin

            * Organisation admin of the project

        Args:
            dataset_hash: The Dataset ID
            dataset_access_settings: Set the dataset_access_settings if you would like to change the defaults.
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

    def get_project(self, project_hash: str) -> Project:
        """
        Get the Project class to access project fields and manipulate a project.

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
        querier = Querier(self._config.config, resource_type=TYPE_PROJECT, resource_id=project_hash)
        client = EncordClientProject(querier=querier, config=self._config.config, api_client=self._api_client)
        project_orm = client.get_project_v2()

        orm_ontology = querier.basic_getter(OrmOntology, project_orm.ontology_hash)
        project_ontology = Ontology(querier, orm_ontology, self._api_client)

        return Project(client, project_orm, project_ontology, self._api_client)

    def get_ontology(self, ontology_hash: str) -> Ontology:
        querier = Querier(self._config.config, resource_type=TYPE_ONTOLOGY, resource_id=ontology_hash)
        orm_ontology = querier.basic_getter(OrmOntology, ontology_hash)
        return Ontology(querier, orm_ontology, self._api_client)

    @deprecated("0.1.104", alternative=".create_dataset")
    def create_private_dataset(
        self,
        dataset_title: str,
        dataset_type: StorageLocation,
        dataset_description: Optional[str] = None,
    ) -> CreateDatasetResponse:
        """
        DEPRECATED - please use `create_dataset` instead.
        """
        return self.create_dataset(dataset_title, dataset_type, dataset_description)

    def create_dataset(
        self,
        dataset_title: str,
        dataset_type: StorageLocation,
        dataset_description: Optional[str] = None,
        create_backing_folder: bool = True,
    ) -> CreateDatasetResponse:
        """
        Args:
            dataset_title:
                Title of dataset.
            dataset_type:
                StorageLocation type where data will be stored.
            dataset_description:
                Optional description of the dataset.
        Returns:
            CreateDatasetResponse
        """
        dataset = {
            "title": dataset_title,
            "type": dataset_type,
            "create_backing_folder": create_backing_folder,
        }

        if dataset_description:
            dataset["description"] = dataset_description

        result = self._querier.basic_setter(OrmDataset, uid=None, payload=dataset)
        return CreateDatasetResponse.from_dict(result)

    def create_dataset_api_key(
        self, dataset_hash: str, api_key_title: str, dataset_scopes: List[DatasetScope]
    ) -> DatasetAPIKey:
        api_key_payload = {
            "dataset_hash": dataset_hash,
            "title": api_key_title,
            "scopes": list(map(lambda scope: scope.value, dataset_scopes)),
        }
        response = self._querier.basic_setter(DatasetAPIKey, uid=None, payload=api_key_payload)
        return DatasetAPIKey.from_dict(response)

    def get_dataset_api_keys(self, dataset_hash: str) -> List[DatasetAPIKey]:
        api_key_payload = {
            "dataset_hash": dataset_hash,
        }
        api_keys: List[DatasetAPIKey] = self._querier.get_multiple(DatasetAPIKey, uid=None, payload=api_key_payload)
        return api_keys

    def get_or_create_dataset_api_key(self, dataset_hash: str) -> DatasetAPIKey:
        api_key_payload = {
            "dataset_hash": dataset_hash,
        }
        response = self._querier.basic_put(DatasetAPIKey, uid=None, payload=api_key_payload)
        return DatasetAPIKey.from_dict(response)

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
    ) -> List[Dict[str, Any]]:
        """
        List either all (if called with no arguments) or matching datasets the user has access to.

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
            list of (role, dataset) pairs for datasets  matching filter conditions.
        """
        properties_filter = self.__validate_filter(locals())
        # a hack to be able to share validation code without too much c&p
        data = self._querier.get_multiple(
            DatasetWithUserRole,
            payload={
                "filter": properties_filter,
                "enable_storage_api": True,
            },
        )

        def convert_dates(dataset):
            dataset["created_at"] = parse_datetime(dataset["created_at"])
            dataset["last_edited_at"] = parse_datetime(dataset["last_edited_at"])
            return dataset

        return [
            {"dataset": DatasetInfo(**convert_dates(d.dataset)), "user_role": DatasetUserRole(d.user_role)}
            for d in data
        ]

    @staticmethod
    def create_with_ssh_private_key(
        ssh_private_key: Optional[str] = None,
        password: Optional[str] = None,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
        ssh_private_key_path: Optional[str | Path] = None,
        **kwargs,
    ) -> EncordUserClient:
        """
        Creates an instance of EncordUserClient authenticated with private SSH key.
        Accepts the private key content, path to key file, that can be provided as method parameters or as following environment variables:

        * **ENCORD_SSH_KEY**: environment variable with the private key content
        * **ENCORD_SSH_KEY_FILE**: environment variable with the path to the key file

        Args:
            ssh_private_key: the private key content
            ssh_private_key_path: the pah to the private key file
            password: private key password
        """

        if ssh_private_key_path is not None:
            if isinstance(ssh_private_key_path, str):
                ssh_private_key_path = Path(ssh_private_key_path)

            ssh_private_key = ssh_private_key_path.read_text(encoding="ascii")

        if not ssh_private_key:
            ssh_private_key = get_env_ssh_key()

        config = SshConfig.from_ssh_private_key(
            ssh_private_key, password, requests_settings=requests_settings, **kwargs
        )
        user_config = UserConfig(config)
        querier = Querier(user_config)
        return EncordUserClient(user_config, querier)

    @staticmethod
    def create_with_bearer_token(
        token: str, *, requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS, **kwargs
    ) -> EncordUserClient:
        config = BearerConfig.from_bearer_token(token=token, requests_settings=requests_settings, **kwargs)
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
        """
        List either all (if called with no arguments) or matching projects the user has access to.

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
            list of (role, projects) pairs for project matching filter conditions.
        """
        properties_filter = self.__validate_filter(locals())
        # a hack to be able to share validation code without too much c&p
        data = self._querier.get_multiple(ProjectWithUserRole, payload={"filter": properties_filter})
        return [{"project": OrmProject(p.project), "user_role": ProjectUserRole(p.user_role)} for p in data]

    def create_project(
        self,
        project_title: str,
        dataset_hashes: List[str],
        project_description: str = "",
        ontology_hash: str = "",
        workflow_settings: ProjectWorkflowSettings = ManualReviewWorkflowSettings(),
        workflow_template_hash: Optional[str] = None,
    ) -> str:
        """
        Creates a new project and returns its uid ('project_hash')

        Args:
            project_title: the title of the project
            dataset_hashes: a list of the dataset uids that the project will use
            project_description: the optional description of the project
            ontology_hash: the uid of an ontology to be used. If omitted, a new empty ontology will be created
            workflow_settings: selects and configures the type of the quality control workflow to use, See :class:`encord.orm.project.ProjectWorkflowSettings` for details. If omitted, :class:`~encord.orm.project.ManualReviewWorkflowSettings` is used.
            workflow_template_hash: project will be created using a workflow based on the template provided.
        Returns:
            the uid of the project.
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

    def create_project_api_key(self, project_hash: str, api_key_title: str, scopes: List[APIKeyScopes]) -> str:
        """
        Returns:
            The created project API key.
        """
        payload = {"title": api_key_title, "scopes": list(map(lambda scope: scope.value, scopes))}

        return self._querier.basic_setter(ProjectAPIKey, uid=project_hash, payload=payload)

    def get_project_api_keys(self, project_hash: str) -> List[ProjectAPIKey]:
        return self._querier.get_multiple(ProjectAPIKey, uid=project_hash)

    def get_or_create_project_api_key(self, project_hash: str) -> str:
        return self._querier.basic_put(ProjectAPIKey, uid=project_hash, payload={})

    @deprecated("0.1.98", ".get_dataset()")
    def get_dataset_client(
        self,
        dataset_hash: str,
        dataset_access_settings: DatasetAccessSettings = DEFAULT_DATASET_ACCESS_SETTINGS,
        **kwargs,
    ) -> EncordClientDataset:
        """
        DEPRECATED - prefer using :meth:`get_dataset()` instead.
        """
        dataset_api_key: DatasetAPIKey = self.get_or_create_dataset_api_key(dataset_hash)
        return EncordClientDataset.initialise(
            dataset_hash,
            dataset_api_key.api_key,
            requests_settings=self._config.requests_settings,
            dataset_access_settings=dataset_access_settings,
        )

    @deprecated("0.1.98", ".get_project()")
    def get_project_client(self, project_hash: str, **kwargs) -> Union[EncordClientProject, EncordClientDataset]:
        """
        DEPRECATED - prefer using :meth:`get_project()` instead.
        """
        project_api_key: str = self.get_or_create_project_api_key(project_hash)
        return EncordClient.initialise(
            project_hash, project_api_key, requests_settings=self._config.requests_settings, **kwargs
        )

    def create_project_from_cvat(
        self,
        import_method: ImportMethod,
        dataset_name: str,
        review_mode: ReviewMode = ReviewMode.LABELLED,
        max_workers: Optional[int] = None,
        *,
        transform_bounding_boxes_to_polygons=False,
    ) -> Union[CvatImporterSuccess, CvatImporterError]:
        """
        Export your CVAT project with the "CVAT for images 1.1" option and use this function to import
            your images and annotations into encord. Ensure that during you have the "Save images"
            checkbox enabled when exporting from CVAT.

        Args:
            import_method:
                The chosen import method. See the `ImportMethod` class for details.
            dataset_name:
                The name of the dataset that will be created.
            review_mode:
                Set how much interaction is needed from the labeler and from the reviewer for the CVAT labels.
                    See the `ReviewMode` documentation for more details.
            max_workers:
                DEPRECATED: This argument will be ignored
            transform_bounding_boxes_to_polygons:
                All instances of CVAT bounding boxes will be converted to polygons in the final Encord project.

        Returns:
            CvatImporterSuccess: If the project was successfully imported.
            CvatImporterError: If the project could not be imported.

        Raises:
            ValueError:
                If the CVAT directory has an invalid format.
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
            annotations_base64 = base64.b64encode(f.read()).decode("utf-8")

        images_paths, used_base_path = self.__get_images_paths(annotations_base64, images_directory_path)

        log.info("Starting image upload.")
        dataset_hash, image_title_to_image = self.__upload_cvat_images(images_paths, used_base_path, dataset_name)
        log.info("Image upload completed.")

        # This is a bit hacky, but allows more flexibility for CVAT project imports
        if import_method.map_filename_to_cvat_name:
            image_title_to_image = {
                import_method.map_filename_to_cvat_name(key): value for key, value in image_title_to_image.items()
            }

        payload = {
            "cvat": {"annotations_base64": annotations_base64},
            "dataset_hash": dataset_hash,
            "image_title_to_image": image_title_to_image,
            "review_mode": review_mode,
            "transform_bounding_boxes_to_polygons": transform_bounding_boxes_to_polygons,
        }

        log.info("Starting project import. This may take a few minutes.")
        server_ret = self._querier.basic_setter(ProjectImporter, uid=None, payload=payload)

        if "success" in server_ret:
            success = server_ret["success"]
            return CvatImporterSuccess(
                project_hash=success["project_hash"],
                dataset_hash=dataset_hash,
                issues=Issues.from_dict(success["issues"]),
            )
        elif "error" in server_ret:
            error = server_ret["error"]
            return CvatImporterError(dataset_hash=dataset_hash, issues=Issues.from_dict(error["issues"]))
        else:
            raise ValueError("The api server responded with an invalid payload.")

    def __get_images_paths(self, annotations_base64: str, images_directory_path: Path) -> Tuple[List[Path], Path]:
        payload = {"annotations_base64": annotations_base64}
        project_info = self._querier.basic_setter(ProjectImporterCvatInfo, uid=None, payload=payload)
        if "error" in project_info:
            message = project_info["error"]["message"]
            raise ValueError(message)

        export_type = project_info["success"]["export_type"]
        if export_type == CvatExportType.PROJECT:
            default_path = images_directory_path.joinpath("default")
            if default_path not in list(images_directory_path.iterdir()):
                raise ValueError("The expected directory 'default' was not found.")

            used_base_path = default_path
            # NOTE: it is possible that here we also need to use the __get_recursive_image_paths
            images = list(default_path.iterdir())

        elif export_type == CvatExportType.TASK:
            used_base_path = images_directory_path
            images = self.__get_recursive_image_paths(images_directory_path)
        else:
            raise ValueError(
                f"Received an unexpected response `{project_info}` from the server. Project import aborted."
            )

        if not images:
            raise ValueError("No images found in the provided data folder.")
        return images, used_base_path

    @staticmethod
    def __get_recursive_image_paths(images_directory_path: Path) -> List[Path]:
        """Recursively get all the images in all the sub folders."""
        return [file for file in images_directory_path.glob("**/*") if file.is_file()]

    def __upload_cvat_images(
        self, images_paths: List[Path], used_base_path: Path, dataset_name: str
    ) -> Tuple[str, Dict[str, Dict[str, str]]]:
        """
        This function does not create any image groups yet.
        Returns:
            * The created dataset_hash
            * A map from an image title to the image hash which is stored in the DB.
        """

        dataset_info = self.create_dataset(dataset_name, StorageLocation.CORD_STORAGE)

        dataset_hash = dataset_info.dataset_hash

        dataset = self.get_dataset(
            dataset_hash,
        )
        querier = dataset._client._querier

        successful_uploads = upload_to_signed_url_list(
            file_paths=images_paths,
            config=self._config,
            querier=querier,
            orm_class=Images,
            cloud_upload_settings=CloudUploadSettings(),
        )
        if len(images_paths) != len(successful_uploads):
            raise RuntimeError("Could not upload all the images successfully. Aborting CVAT upload.")

        image_title_to_image = {}
        for image_path, successful_upload in zip(images_paths, successful_uploads):
            trimmed_image_path_str = str(image_path.relative_to(used_base_path))
            image_title_to_image[trimmed_image_path_str] = {
                "data_hash": successful_upload.data_hash,
                "file_link": successful_upload.file_link,
                "title": successful_upload.title,
            }

        return dataset_hash, image_title_to_image

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self._querier.get_multiple(CloudIntegration)

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
    ) -> List[Dict]:
        """
        List either all (if called with no arguments) or matching ontologies the user has access to.

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
            list of (role, projects) pairs for ontologies matching filter conditions.
        """
        properties_filter = self.__validate_filter(locals())
        # a hack to be able to share validation code without too much c&p
        data = self._querier.get_multiple(OntologyWithUserRole, payload={"filter": properties_filter})
        retval: List[Dict] = []
        for row in data:
            ontology = OrmOntology.from_dict(row.ontology)
            querier = Querier(self._config, resource_type=TYPE_ONTOLOGY, resource_id=ontology.ontology_hash)
            retval.append(
                {
                    "ontology": Ontology(querier, ontology, api_client=self._api_client),
                    "user_role": OntologyUserRole(row.user_role),
                }
            )
        return retval

    def create_ontology(
        self,
        title: str,
        description: str = "",
        structure: Optional[OntologyStructure] = None,
    ) -> Ontology:
        try:
            structure_dict = structure.to_dict() if structure else OntologyStructure().to_dict()
        except ValueError as e:
            raise ValueError("Can't create an Ontology containing a Classification without any attributes. " + str(e))

        ontology = {
            "title": title,
            "description": description,
            "editor": structure_dict,
        }

        retval = self._querier.basic_setter(OrmOntology, uid=None, payload=ontology)
        ontology = OrmOntology.from_dict(retval)
        querier = Querier(self._config, resource_type=TYPE_ONTOLOGY, resource_id=ontology.ontology_hash)

        return Ontology(querier, ontology, self._api_client)

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
        """
        List all groups belonging to the user's current organization.
        """
        page = self._api_client.get("user/current-organisation/groups", params=None, result_type=Page[OrmGroup])
        yield from page.results

    def deidentify_dicom_files(
        self,
        dicom_urls: List[str],
        integration_hash: str,
        redact_dicom_tags: bool = True,
        redact_pixels_mode: DeidentifyRedactTextMode = DeidentifyRedactTextMode.REDACT_NO_TEXT,
        save_conditions: Optional[List[SaveDeidentifiedDicomCondition]] = None,
        upload_dir: Optional[str] = None,
    ) -> List[str]:
        """
        Deidentify DICOM files in external storage.
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
            dicom_urls: a list of urls to DICOM files, e.g.
                `[ "https://s3.region-code.amazonaws.com/bucket-name/dicom-file-input.dcm" ]`
            integration_hash:
                integration_hash parameter of Encord platform external storage integration
            redact_dicom_tags:
                Specifies if DICOM tags redaction should be enabled.
            redact_pixels_mode:
                Specifies which text redaction policy should be applied to pixel data.
            save_conditions:
                Specifies a list of conditions which all have to be true for DICOM deidentified file to be saved.
            upload_dir:
                Specifies a directory that files will be uploaded to. By default, set to None,
                deidentified files will be uploaded to the same directory as source files.
        Returns:
            Function returns list of links pointing to deidentified DICOM files,
            those will be saved to the same bucket and the same directory
            as original files with prefix ( deid_{timestamp}_ ).
            Example output:
            `[ "https://s3.region-code.amazonaws.com/bucket-name/deid_167294769118005312_dicom-file-input.dcm" ]`

        """

        return self._querier.basic_setter(
            DicomDeidentifyTask,
            uid=integration_hash,
            payload={
                "dicom_urls": dicom_urls,
                "redact_dicom_tags": redact_dicom_tags,
                "redact_pixels_mode": redact_pixels_mode.value,
                "save_conditions": [x.to_dict() for x in (save_conditions or [])],
                "upload_dir": upload_dir,
            },
        )

    def create_storage_folder(
        self,
        name: str,
        description: Optional[str] = None,
        client_metadata: Optional[Dict[str, Any]] = None,
        parent_folder: Optional[Union[StorageFolder, UUID]] = None,
    ) -> StorageFolder:
        """
        Create a new storage folder.

        Args:
            name: The name of the folder.
            description: The description of the folder.
            client_metadata: Optional arbitrary metadata to be associated with the folder. Should be a dictionary
                that is JSON-serializable.
            parent_folder: The parent folder of the folder; or `None` if the folder is to be created at the root level.

        Returns:
            The created storage folder. See :class:`encord.storage.StorageFolder` for details.
        """

        return StorageFolder._create_folder(self._api_client, name, description, client_metadata, parent_folder)

    def get_storage_folder(self, folder_uuid: UUID) -> StorageFolder:
        """
        Get a storage folder by its UUID.

        Args:
            folder_uuid: The UUID of the folder to retrieve.

        Returns:
            The storage folder. See :class:`encord.storage.StorageFolder` for details.

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the folder with the given UUID does not exist or
                the user does not have access to it.
        """
        return StorageFolder._get_folder(self._api_client, folder_uuid)

    def get_storage_item(self, item_uuid: UUID, sign_url: bool = False) -> StorageItem:
        """
        Get a storage item by its UUID.

        Args:
            item_uuid: The UUID of the item to retrieve.
            sign_url: If `True`, pre-fetch a signed URL for the item (otherwise the URL will be signed on demand).

        Returns:
            The storage item. See :class:`encord.storage.StorageItem` for details.

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the item with the given UUID does not exist or
                the user does not have access to it.
        """
        return StorageItem._get_item(self._api_client, item_uuid, sign_url)

    def get_storage_items(self, item_uuids: List[UUID], sign_url: bool = False) -> List[StorageItem]:
        """
        Get storage items by their UUIDs, in bulk. Useful for retrieving multiple items at once, e.g. when getting
        items pointed to by :attr:`encord.orm.dataset.DataRow.backing_item_uuid` for all data rows of a dataset.

        Args:
            item_uuids: list of UUIDs of items to retrieve.
            sign_url: If `True`, pre-fetch a signed URLs for the items (otherwise the URLs will be signed on demand).

        Returns:
            A list of storage items. See :class:`encord.storage.StorageItem` for details.

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If some of the items with the given UUIDs do not exist or
                the user does not have access to them.
        """
        return StorageItem._get_items(self._api_client, item_uuids, sign_url)

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
        """
        List top-level storage folders.

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
        """
        Recursively search for storage folders, starting from the top level.

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
        """
        Recursively search for storage items, starting from the root level.

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
        """
        Get collection by unique identifier (UUID).

        Args:
            collection_uuid: The unique identifier of the collection to retrieve.

        Returns:
            The collection. See :class:`encord.collection.Collection` for details.

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the item with the given UUID does not exist or
                the user does not have access to it.
        """
        if isinstance(collection_uuid, str):
            collection_uuid = UUID(collection_uuid)

        return Collection._get_collection(self._api_client, collection_uuid=collection_uuid)

    def list_collections(
        self,
        top_level_folder_uuid: Union[str, UUID, None] = None,
        collection_uuids: List[str | UUID] | None = None,
        page_size: Optional[int] = None,
    ) -> Generator[Collection]:
        """
        Get collections by top level folder or list of collection IDs.
        If both top_level_folder_uuid and collection_uuid_list are preset
        then the intersection of the two conditions is returned.

        Args:
            top_level_folder_uuid: The unique identifier of the top level folder.
            collection_uuids: The unique identifiers (UUIDs) of the collections to retrieve.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.
        Returns:
            The list of collections which match the given criteria.

        Raises:
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
        """
        Delete a collection by its UUID if it exists.

        Args:
            collection_uuid: The unique identifier (UUID) of the collection to delete.

        Returns:
            None

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        if isinstance(collection_uuid, str):
            collection_uuid = UUID(collection_uuid)
        Collection._delete_collection(self._api_client, collection_uuid)

    def create_collection(
        self, top_level_folder_uuid: Union[str, UUID], name: str, description: str = ""
    ) -> Collection:
        """
        Create a collection.

        Args:
            top_level_folder_uuid: The unique identifier (UUID) of the folder that the collection is created in.
            name: The name of the collection.
            description: The description of the collection.

        Returns:
            Collection: Newly created collection.

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to the folder.
        """
        if isinstance(top_level_folder_uuid, str):
            top_level_folder_uuid = UUID(top_level_folder_uuid)
        new_uuid = Collection._create_collection(self._api_client, top_level_folder_uuid, name, description)
        return self.get_collection(new_uuid)

    def get_filter_preset(self, preset_uuid: Union[str, UUID]) -> FilterPreset:
        """
        Get a preset by its unique identifier (UUID).

        Args:
            preset_uuid: The unique identifier of the preset to retrieve.

        Returns:
            The preset. See :class:`encord.preset.Preset` for details.

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the item with the given UUID does not exist or
                the user does not have access to it.
        """
        if isinstance(preset_uuid, str):
            preset_uuid = UUID(preset_uuid)
        return FilterPreset._get_preset(self._api_client, preset_uuid=preset_uuid)

    def get_filter_presets(
        self, preset_uuids: List[Union[str, UUID]] = [], page_size: Optional[int] = None
    ) -> Generator[FilterPreset]:
        """
        Get presets by list of preset unique identifiers (UUIDs).

        Args:
            preset_uuids: The list of unique identifiers (UUIDs) to be retrieved.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.
        Returns:
            The list of presets which match the given criteria.

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        preset_uuids = [UUID(collection) if isinstance(collection, str) else collection for collection in preset_uuids]
        return FilterPreset._get_presets(self._api_client, preset_uuids, page_size=page_size)

    def list_presets(
        self, top_level_folder_uuid: Union[str, UUID, None] = None, page_size: Optional[int] = None
    ) -> Generator[FilterPreset]:
        """
        Get presets by top level folder.

        Args:
            top_level_folder_uuid: The unique identifier of the top level folder.
            page_size (int): Number of items to return per page.  Default if not specified is 100. Maximum value is 1000.

        Returns:
            The list of presets which match the given criteria.

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        if isinstance(top_level_folder_uuid, str):
            top_level_folder_uuid = UUID(top_level_folder_uuid)
        return FilterPreset._list_presets(self._api_client, top_level_folder_uuid, page_size=page_size)

    def delete_preset(self, preset_uuid: Union[str, UUID]) -> None:
        """
        Delete a preset by its unique identifier (UUID) if it exists.

        Args:
            preset_uuid: The uuid/id of the preset to delete.

        Returns:
            None

        Raises:
            :class:`encord.exceptions.AuthorizationError` : If the user does not have access to it.
        """
        if isinstance(preset_uuid, str):
            preset_uuid = UUID(preset_uuid)
        FilterPreset._delete_preset(self._api_client, preset_uuid)


class ListingFilter(Enum):
    """
    Available properties_filter keys for get_projects() and get_datasets().

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
