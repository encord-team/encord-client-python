from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Union

from cord.client import CordClient
from cord.configs import UserConfig
from cord.http.querier import Querier
from cord.http.utils import upload_to_signed_url_list, upload_to_signed_url_list_async
from cord.orm.dataset import SignedImagesURL, Image
from cord.orm.cloud_integration import CloudIntegration
from cord.orm.dataset import Dataset, DatasetType
from cord.orm.dataset import DatasetScope, DatasetAPIKey
from cord.orm.project import Project, ProjectImporter, ReviewMode, ProjectImporterCvatInfo, CvatExportType
from cord.orm.project_api_key import ProjectAPIKey
from cord.utilities.client_utilities import APIKeyScopes

log = logging.getLogger(__name__)


class CordUserClient:
    def __init__(self, user_config: UserConfig, querier: Querier):
        self.user_config = user_config
        self.querier = querier

    def create_private_dataset(self, dataset_title: str, dataset_type: DatasetType, dataset_description: str = None):
        return self.create_dataset(dataset_title, dataset_type, dataset_description)

    def create_dataset(self, dataset_title: str, dataset_type: DatasetType, dataset_description: str = None):
        dataset = {
            'title': dataset_title,
            'type': dataset_type,
        }

        if dataset_description:
            dataset['description'] = dataset_description

        return self.querier.basic_setter(Dataset, uid=None, payload=dataset)

    def create_dataset_api_key(
            self, dataset_hash: str, api_key_title: str, dataset_scopes: List[DatasetScope]) -> DatasetAPIKey:
        api_key_payload = {
            'dataset_hash': dataset_hash,
            'title': api_key_title,
            'scopes': list(map(lambda scope: scope.value, dataset_scopes))
        }
        response = self.querier.basic_setter(DatasetAPIKey, uid=None, payload=api_key_payload)
        return DatasetAPIKey.from_dict(response)

    def get_dataset_api_keys(self, dataset_hash: str) -> List[DatasetAPIKey]:
        api_key_payload = {
            'dataset_hash': dataset_hash,
        }
        api_keys: List[DatasetAPIKey] = self.querier.get_multiple(DatasetAPIKey, uid=None, payload=api_key_payload)
        return api_keys

    @staticmethod
    def create_with_ssh_private_key(ssh_private_key: str, password: str = None, **kwargs) -> CordUserClient:
        user_config = UserConfig.from_ssh_private_key(ssh_private_key, password, **kwargs)
        querier = Querier(user_config)

        return CordUserClient(user_config, querier)

    def create_project(self, project_title: str, dataset_hashes: List[str], project_description: str = "") -> str:
        project = {
            'title': project_title,
            'description': project_description,
            'dataset_hashes': dataset_hashes
        }

        return self.querier.basic_setter(Project, uid=None, payload=project)

    def create_project_api_key(self, project_hash: str, api_key_title: str, scopes: List[APIKeyScopes]) -> str:
        payload = {
            'title': api_key_title,
            'scopes': list(map(lambda scope: scope.value, scopes))
        }

        return self.querier.basic_setter(ProjectAPIKey, uid=project_hash, payload=payload)

    def get_project_api_keys(self, project_hash: str) -> List[ProjectAPIKey]:
        return self.querier.get_multiple(ProjectAPIKey, uid=project_hash)

    def create_project_from_cvat(self,
                                 import_method: ImportMethod,
                                 dataset_name: str,
                                 review_mode: ReviewMode = ReviewMode.LABELLED) \
            -> Union[CvatImporterSuccess, CvatImporterError]:
        """
        Export your CVAT project with the "CVAT for images 1.1" option and use this function to import
            your images and annotations into cord. Ensure that during you have the "Save images"
            checkbox enabled when exporting from CVAT.
        Args:
            import_method:
                The chosen import method. See the `ImportMethod` class for details.
            dataset_name:
                The name of the dataset that will be created.
            review_mode:
                Set how much interaction is needed from the labeler and from the reviewer for the CVAT labels.
                    See the `ReviewMode` documentation for more details.

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
        images_directory_path = directory_path.joinpath('images')
        if images_directory_path not in list(directory_path.iterdir()):
            raise ValueError("The expected directory 'images' was not found.")

        annotations_file_path = directory_path.joinpath("annotations.xml")
        if not annotations_file_path.is_file():
            raise ValueError(f"The file `{annotations_file_path}` does not exist.")

        with annotations_file_path.open('rb') as f:
            annotations_base64 = base64.b64encode(f.read()).decode('utf-8')

        images_paths = self.__get_images_paths(annotations_base64, images_directory_path)

        log.info("Starting image upload.")
        dataset_hash, image_title_to_image_hash_map = self.__upload_cvat_images(images_paths, dataset_name)
        log.info("Image upload completed.")

        payload = {
            "cvat": {
                "annotations_base64": annotations_base64,
            },
            "dataset_hash": dataset_hash,
            "image_title_to_image_hash_map": image_title_to_image_hash_map,
            "review_mode": ReviewMode.to_string(review_mode)
        }

        log.info("Starting project import. This may take a few minutes.")
        server_ret = self.querier.basic_setter(ProjectImporter, uid=None, payload=payload)

        if "success" in server_ret:
            success = server_ret["success"]
            return CvatImporterSuccess(
                project_hash=success["project_hash"],
                dataset_hash=dataset_hash,
                issues=Issues.from_dict(success["issues"])
            )
        elif "error" in server_ret:
            error = server_ret["error"]
            return CvatImporterError(
                dataset_hash=dataset_hash,
                issues=Issues.from_dict(error["issues"])
            )
        else:
            raise ValueError("The api server responded with an invalid payload.")

    def __get_images_paths(self, annotations_base64: str, images_directory_path: Path) -> List[Path]:
        payload = {
            "annotations_base64": annotations_base64
        }
        project_info = self.querier.basic_setter(ProjectImporterCvatInfo, uid=None, payload=payload)
        export_type = project_info["export_type"]
        if export_type == CvatExportType.PROJECT.value:
            default_path = images_directory_path.joinpath('default')
            if default_path not in list(images_directory_path.iterdir()):
                raise ValueError("The expected directory 'default' was not found.")

            images = list(default_path.iterdir())
        elif export_type == CvatExportType.TASK.value:
            images = list(images_directory_path.iterdir())
        else:
            raise ValueError("Received an unexpected response from the server. Project import aborted.")

        if not images:
            raise ValueError(f"No images found in the provided data folder.")
        return images

    def __upload_cvat_images(self,
                             images_paths: List[Path],
                             dataset_name: str) -> Tuple[str, Dict[str, str]]:
        """
        This function does not create any image groups yet.
        Returns:
            * The created dataset_hash
            * A map from an image title to the image hash which is stored in the DB.
        """

        short_names = list(map(lambda x: x.name, images_paths))
        file_path_strings = list(map(lambda x: str(x), images_paths))
        dataset = self.create_dataset(dataset_name, DatasetType.CORD_STORAGE)

        dataset_hash = dataset["dataset_hash"]

        dataset_api_key: DatasetAPIKey = self.create_dataset_api_key(
            dataset_hash,
            dataset_name + " - Full Access API Key",
            [DatasetScope.READ, DatasetScope.WRITE])

        client = CordClient.initialise(
            dataset_hash,
            dataset_api_key.api_key,
            domain=self.user_config.domain,
        )

        signed_urls = client._querier.basic_getter(
            SignedImagesURL,
            uid=short_names
        )
        asyncio.run(upload_to_signed_url_list_async(
            file_path_strings, signed_urls, client._querier, Image
        ))

        image_title_to_image_hash_map = dict(map(lambda x: (x.title, x.data_hash), signed_urls))

        return dataset_hash, image_title_to_image_hash_map

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self.querier.get_multiple(CloudIntegration)


@dataclass
class LocalImport:
    """
    file_path: Supply the path of the exported folder which contains the images and `annotations.xml` file. Make
    sure to select "Save images" when exporting your CVAT Task or Project.
    """
    file_path: str


ImportMethod = Union[LocalImport]
"""Using images/videos in cloud storage as an alternative import method will be supported in the future."""


@dataclass
class Issue:
    """
    For each `issue_type` there may be multiple occurrences which are documented in the `instances`. The `instances`
    list can provide additional information on how the issue was encountered. If there is no additional information
    available, the `instances` list will be empty.
    """
    issue_type: str
    instances: List[str]


@dataclass
class Issues:
    """
    Any issues that came up during importing a project. These usually come from incompatibilities between data saved
    on different platforms.
    """
    errors: List[Issue]
    warnings: List[Issue]
    infos: List[Issue]

    @staticmethod
    def from_dict(d: dict) -> "Issues":
        errors, warnings, infos = [], [], []
        for error in d["errors"]:
            issue = Issue(
                issue_type=error["issue_type"],
                instances=error["instances"]
            )
            errors.append(issue)
        for warning in d["warnings"]:
            issue = Issue(
                issue_type=warning["issue_type"],
                instances=warning["instances"]
            )
            warnings.append(issue)
        for info in d["infos"]:
            issue = Issue(
                issue_type=info["issue_type"],
                instances=info["instances"]
            )
            infos.append(issue)
        return Issues(
            errors=errors,
            warnings=warnings,
            infos=infos
        )


@dataclass
class CvatImporterSuccess:
    project_hash: str
    dataset_hash: str
    issues: Issues


@dataclass
class CvatImporterError:
    dataset_hash: str
    issues: Issues
