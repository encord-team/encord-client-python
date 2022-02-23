from __future__ import annotations

import asyncio
import base64
import datetime
from dataclasses import dataclass
import logging
from enum import Enum
from pathlib import Path
from typing import List, Dict, Tuple, Union, Optional

import dateutil

from encord.client import EncordClient, EncordClientProject, EncordClientDataset
from encord.configs import UserConfig
from encord.http.querier import Querier
from encord.http.utils import upload_to_signed_url_list
from encord.orm.dataset import SignedImagesURL, Image, CreateDatasetResponse, DatasetInfo, DatasetUserRole
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import Dataset, StorageLocation
from encord.orm.dataset_with_user_role import DatasetWithUserRole
from encord.orm.dataset import DatasetScope, DatasetAPIKey
from encord.orm.project import (
    Project,
    ProjectImporter,
    ReviewMode,
    ProjectImporterCvatInfo,
    CvatExportType,
)
from encord.orm.project_api_key import ProjectAPIKey
from encord.orm.project_with_user_role import ProjectWithUserRole
from encord.utilities.client_utilities import (
    APIKeyScopes,
    CvatImporterSuccess,
    Issues,
    CvatImporterError,
    LocalImport,
    ImportMethod,
)
from encord.utilities.project_user import ProjectUserRole

log = logging.getLogger(__name__)


class EncordUserClient:
    def __init__(self, user_config: UserConfig, querier: Querier):
        self.user_config = user_config
        self.querier = querier


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
        }

        if dataset_description:
            dataset["description"] = dataset_description

        result = self.querier.basic_setter(Dataset, uid=None, payload=dataset)
        return CreateDatasetResponse.from_dict(result)


    def create_dataset_api_key(
            self, dataset_hash: str, api_key_title: str, dataset_scopes: List[DatasetScope]
    ) -> DatasetAPIKey:
        api_key_payload = {
            "dataset_hash": dataset_hash,
            "title": api_key_title,
            "scopes": list(map(lambda scope: scope.value, dataset_scopes)),
        }
        response = self.querier.basic_setter(DatasetAPIKey, uid=None, payload=api_key_payload)
        return DatasetAPIKey.from_dict(response)


    def get_dataset_api_keys(self, dataset_hash: str) -> List[DatasetAPIKey]:
        api_key_payload = {
            "dataset_hash": dataset_hash,
        }
        api_keys: List[DatasetAPIKey] = self.querier.get_multiple(DatasetAPIKey, uid=None, payload=api_key_payload)
        return api_keys


    def get_or_create_dataset_api_key(self, dataset_hash: str) -> DatasetAPIKey:
        api_key_payload = {
            "dataset_hash": dataset_hash,
        }
        response = self.querier.basic_put(DatasetAPIKey, uid=None, payload=api_key_payload)
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
    ) -> List[Dict]:
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
        data = self.querier.get_multiple(DatasetWithUserRole, payload={'filter': properties_filter})


        def convert_dates(dataset):
            dataset['created_at'] = dateutil.parser.isoparse(dataset['created_at'])
            dataset['last_edited_at'] = dateutil.parser.isoparse(dataset['last_edited_at'])
            return dataset

        return [{"dataset": DatasetInfo(**convert_dates(d.dataset)), "user_role": DatasetUserRole(d.user_role)} for d in data]


    @staticmethod
    def create_with_ssh_private_key(ssh_private_key: str, password: str = None, **kwargs) -> EncordUserClient:
        user_config = UserConfig.from_ssh_private_key(ssh_private_key, password, **kwargs)
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
        data = self.querier.get_multiple(ProjectWithUserRole, payload={'filter': properties_filter})
        return [{"project": Project(p.project), "user_role": ProjectUserRole(p.user_role)} for p in data]


    def create_project(self, project_title: str, dataset_hashes: List[str], project_description: str = "") -> str:
        project = {"title": project_title, "description": project_description, "dataset_hashes": dataset_hashes}

        return self.querier.basic_setter(Project, uid=None, payload=project)


    def create_project_api_key(self, project_hash: str, api_key_title: str, scopes: List[APIKeyScopes]) -> str:
        """
        Returns:
            The created project API key.
        """
        payload = {"title": api_key_title, "scopes": list(map(lambda scope: scope.value, scopes))}

        return self.querier.basic_setter(ProjectAPIKey, uid=project_hash, payload=payload)


    def get_project_api_keys(self, project_hash: str) -> List[ProjectAPIKey]:
        return self.querier.get_multiple(ProjectAPIKey, uid=project_hash)


    def get_or_create_project_api_key(self, project_hash: str) -> str:
        return self.querier.basic_put(ProjectAPIKey, uid=project_hash, payload={})


    def get_dataset_client(self, dataset_hash: str, **kwargs) -> Union[EncordClientProject, EncordClientDataset]:
        dataset_api_key: DatasetAPIKey = self.get_or_create_dataset_api_key(dataset_hash)
        return EncordClient.initialise(dataset_hash, dataset_api_key.api_key, **kwargs)


    def get_project_client(self, project_hash: str, **kwargs) -> Union[EncordClientProject, EncordClientDataset]:
        project_api_key: str = self.get_or_create_project_api_key(project_hash)
        return EncordClient.initialise(project_hash, project_api_key, **kwargs)


    def create_project_from_cvat(
            self,
            import_method: ImportMethod,
            dataset_name: str,
            review_mode: ReviewMode = ReviewMode.LABELLED,
            max_workers: Optional[int] = None,
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
                Number of workers for parallel image upload. If set to None, this will be the number of CPU cores
                available on the machine.

        Returns:
            CvatImporterSuccess: If the project was successfully imported.
            CvatImporterError: If the project could not be imported.

        Raises:
            ValueError:
                If the CVAT directory has an invalid format.
        """
        if type(import_method) != LocalImport:
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

        images_paths = self.__get_images_paths(annotations_base64, images_directory_path)

        log.info("Starting image upload.")
        dataset_hash, image_title_to_image_hash_map = self.__upload_cvat_images(images_paths, dataset_name, max_workers)
        log.info("Image upload completed.")

        payload = {
            "cvat": {
                "annotations_base64": annotations_base64,
            },
            "dataset_hash": dataset_hash,
            "image_title_to_image_hash_map": image_title_to_image_hash_map,
            "review_mode": review_mode.value,
        }

        log.info("Starting project import. This may take a few minutes.")
        server_ret = self.querier.basic_setter(ProjectImporter, uid=None, payload=payload)

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


    def __get_images_paths(self, annotations_base64: str, images_directory_path: Path) -> List[Path]:
        payload = {"annotations_base64": annotations_base64}
        project_info = self.querier.basic_setter(ProjectImporterCvatInfo, uid=None, payload=payload)
        if "error" in project_info:
            message = project_info["error"]["message"]
            raise ValueError(message)

        export_type = project_info["success"]["export_type"]
        if export_type == CvatExportType.PROJECT.value:
            default_path = images_directory_path.joinpath("default")
            if default_path not in list(images_directory_path.iterdir()):
                raise ValueError("The expected directory 'default' was not found.")

            images = list(default_path.iterdir())
        elif export_type == CvatExportType.TASK.value:
            images = list(images_directory_path.iterdir())
        else:
            raise ValueError(
                f"Received an unexpected response `{project_info}` from the server. Project import aborted."
            )

        if not images:
            raise ValueError(f"No images found in the provided data folder.")
        return images


    def __upload_cvat_images(
            self, images_paths: List[Path], dataset_name: str, max_workers: int
    ) -> Tuple[str, Dict[str, str]]:
        """
        This function does not create any image groups yet.
        Returns:
            * The created dataset_hash
            * A map from an image title to the image hash which is stored in the DB.
        """

        short_names = list(map(lambda x: x.name, images_paths))
        file_path_strings = list(map(lambda x: str(x), images_paths))
        dataset = self.create_dataset(dataset_name, StorageLocation.CORD_STORAGE)

        dataset_hash = dataset.dataset_hash

        dataset_api_key: DatasetAPIKey = self.create_dataset_api_key(
            dataset_hash, dataset_name + " - Full Access API Key", [DatasetScope.READ, DatasetScope.WRITE]
        )

        client = EncordClient.initialise(
            dataset_hash,
            dataset_api_key.api_key,
            domain=self.user_config.domain,
        )

        signed_urls = client._querier.basic_getter(SignedImagesURL, uid=short_names)
        upload_to_signed_url_list(file_path_strings, signed_urls, client._querier, Image, max_workers)

        image_title_to_image_hash_map = dict(map(lambda x: (x.title, x.data_hash), signed_urls))

        return dataset_hash, image_title_to_image_hash_map


    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self.querier.get_multiple(CloudIntegration)


    def __validate_filter(self, properties_filter: Dict) -> Dict:
        if not isinstance(properties_filter, dict):
            raise ValueError("Filter should be a dictionary")

        valid_filters = set([f.value for f in ListingFilter])

        ret = dict()

        # be relaxed with what we receive: translate raw strings to enum values
        for (clause, val) in properties_filter.items():
            if val is None:
                continue

            if isinstance(clause, str) and clause in valid_filters:
                clause = ListingFilter(clause)

            if clause not in ListingFilter:
                continue

            if clause.value.endswith("before") or clause.value.endswith("after"):
                if isinstance(val, str):
                    val = dateutil.parser.isoparse(val)
                if isinstance(val, datetime.datetime):
                    val = val.isoformat()
                else:
                    raise ValueError(f"Value for {clause.name} filter should be a datetime")

            ret[clause.value] = val

        return ret


class ListingFilter(Enum):
    """
    Available properties_filter keys for get_projects() and get_datasets().

    The values for *_before and *_after should be datetime objects.
    """
    TITLE_EQ = "title_eq"
    TITLE_LIKE = "title_like"
    DESC_EQ = "desc_eq"
    DESC_LIKE = "desc_like"
    CREATED_BEFORE = "created_before"
    CREATED_AFTER = "created_after"
    EDITED_BEFORE = "edited_before"
    EDITED_AFTER = "edited_after"


CordUserClient = EncordUserClient
