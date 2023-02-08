from __future__ import annotations

import base64
import datetime
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import dateutil

# add this for backward compatible class comparisons
from cord.utilities.client_utilities import LocalImport as CordLocalImport
from encord.client import EncordClient, EncordClientDataset, EncordClientProject
from encord.configs import SshConfig, UserConfig, get_env_ssh_key
from encord.constants.string_constants import TYPE_DATASET, TYPE_ONTOLOGY, TYPE_PROJECT
from encord.dataset import Dataset
from encord.http.constants import DEFAULT_REQUESTS_SETTINGS, RequestsSettings
from encord.http.querier import Querier
from encord.http.utils import (
    CloudUploadSettings,
    upload_images_to_encord,
    upload_to_signed_url_list,
)
from encord.objects.ontology_labels_impl import Ontology as OrmOntology
from encord.objects.ontology_labels_impl import OntologyStructure
from encord.ontology import Ontology
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import DEFAULT_DATASET_ACCESS_SETTINGS, CreateDatasetResponse
from encord.orm.dataset import Dataset as OrmDataset
from encord.orm.dataset import (
    DatasetAccessSettings,
    DatasetAPIKey,
    DatasetInfo,
    DatasetScope,
    DatasetUserRole,
    DicomDeidentifyTask,
    Images,
    StorageLocation,
)
from encord.orm.dataset_with_user_role import DatasetWithUserRole
from encord.orm.project import (
    BenchmarkQaWorkflowSettings,
    CvatExportType,
    ManualReviewWorkflowSettings,
)
from encord.orm.project import Project as OrmProject
from encord.orm.project import (
    ProjectImporter,
    ProjectImporterCvatInfo,
    ProjectWorkflowSettings,
    ProjectWorkflowType,
    ReviewMode,
)
from encord.orm.project_api_key import ProjectAPIKey
from encord.orm.project_with_user_role import ProjectWithUserRole
from encord.project import Project
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
    def __init__(self, user_config: UserConfig, querier: Querier):
        self.user_config = user_config
        self.querier = querier

    def get_dataset(
        self, dataset_hash: str, dataset_access_settings: DatasetAccessSettings = DEFAULT_DATASET_ACCESS_SETTINGS
    ) -> Dataset:
        """
        Get the Project class to access project fields and manipulate a project.

        You will only have access to this project if you are one of the following

            * Dataset admin

            * Organisation admin of the project

        Args:
            dataset_hash: The Dataset ID
            dataset_access_settings: Set the dataset_access_settings if you would like to change the defaults.
        """
        config = SshConfig(self.user_config, resource_type=TYPE_DATASET, resource_id=dataset_hash)
        querier = Querier(config)
        client = EncordClientDataset(querier=querier, config=config, dataset_access_settings=dataset_access_settings)
        return Dataset(client)

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
        config = SshConfig(self.user_config, resource_type=TYPE_PROJECT, resource_id=project_hash)
        querier = Querier(config)
        client = EncordClientProject(querier=querier, config=config)
        return Project(client)

    def get_ontology(self, ontology_hash: str) -> Ontology:
        config = SshConfig(self.user_config, resource_type=TYPE_ONTOLOGY, resource_id=ontology_hash)
        querier = Querier(config)
        return Ontology(querier, config)

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

        result = self.querier.basic_setter(OrmDataset, uid=None, payload=dataset)
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
        data = self.querier.get_multiple(DatasetWithUserRole, payload={"filter": properties_filter})

        def convert_dates(dataset):
            dataset["created_at"] = dateutil.parser.isoparse(dataset["created_at"])
            dataset["last_edited_at"] = dateutil.parser.isoparse(dataset["last_edited_at"])
            return dataset

        return [
            {"dataset": DatasetInfo(**convert_dates(d.dataset)), "user_role": DatasetUserRole(d.user_role)}
            for d in data
        ]

    @staticmethod
    def create_with_ssh_private_key(
        ssh_private_key: Optional[str] = None,
        password: str = None,
        requests_settings: RequestsSettings = DEFAULT_REQUESTS_SETTINGS,
        **kwargs,
    ) -> EncordUserClient:
        if not ssh_private_key:
            ssh_private_key = get_env_ssh_key()

        user_config = UserConfig.from_ssh_private_key(
            ssh_private_key, password, requests_settings=requests_settings, **kwargs
        )
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
        data = self.querier.get_multiple(ProjectWithUserRole, payload={"filter": properties_filter})
        return [{"project": OrmProject(p.project), "user_role": ProjectUserRole(p.user_role)} for p in data]

    def create_project(
        self,
        project_title: str,
        dataset_hashes: List[str],
        project_description: str = "",
        ontology_hash: str = "",
        workflow_settings: ProjectWorkflowSettings = ManualReviewWorkflowSettings(),
    ) -> str:
        """
        Creates a new project and returns its uid ('project_hash')

        Args:
            project_title: the title of the project
            dataset_hashes: a list of the dataset uids that the project will use
            project_description: the optional description of the project
            ontology_hash: the uid of an ontology to be used. If omitted, a new empty ontology will be created
            workflow_settings: selects and configures the type of the quality control workflow to use, See :class:`encord.orm.project.ProjectWorkflowSettings` for details. If omitted, :class:`~encord.orm.project.ManualReviewWorkflowSettings` is used.

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

        return self.querier.basic_setter(OrmProject, uid=None, payload=project)

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
            requests_settings=self.user_config.requests_settings,
            dataset_access_settings=dataset_access_settings,
        )

    def get_project_client(self, project_hash: str, **kwargs) -> Union[EncordClientProject, EncordClientDataset]:
        """
        DEPRECATED - prefer using :meth:`get_project()` instead.
        """
        project_api_key: str = self.get_or_create_project_api_key(project_hash)
        return EncordClient.initialise(
            project_hash, project_api_key, requests_settings=self.user_config.requests_settings, **kwargs
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
        if not (type(import_method) == LocalImport or type(import_method) == CordLocalImport):
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
        dataset_hash, image_title_to_image_hash_map = self.__upload_cvat_images(
            images_paths, used_base_path, dataset_name
        )
        log.info("Image upload completed.")

        payload = {
            "cvat": {
                "annotations_base64": annotations_base64,
            },
            "dataset_hash": dataset_hash,
            "image_title_to_image_hash_map": image_title_to_image_hash_map,
            "review_mode": review_mode.value,
            "transform_bounding_boxes_to_polygons": transform_bounding_boxes_to_polygons,
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

    def __get_images_paths(self, annotations_base64: str, images_directory_path: Path) -> Tuple[List[Path], Path]:
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

            used_base_path = default_path
            # NOTE: it is possible that here we also need to use the __get_recursive_image_paths
            images = list(default_path.iterdir())

        elif export_type == CvatExportType.TASK.value:
            used_base_path = images_directory_path
            images = self.__get_recursive_image_paths(images_directory_path)
        else:
            raise ValueError(
                f"Received an unexpected response `{project_info}` from the server. Project import aborted."
            )

        if not images:
            raise ValueError(f"No images found in the provided data folder.")
        return images, used_base_path

    @staticmethod
    def __get_recursive_image_paths(images_directory_path: Path) -> List[Path]:
        """Recursively get all the images in all the sub folders."""
        ret = []
        for file in images_directory_path.glob("**/*"):
            if file.is_file():
                ret.append(file)
        return ret

    def __upload_cvat_images(
        self, images_paths: List[Path], used_base_path: Path, dataset_name: str
    ) -> Tuple[str, Dict[str, str]]:
        """
        This function does not create any image groups yet.
        Returns:
            * The created dataset_hash
            * A map from an image title to the image hash which is stored in the DB.
        """

        file_path_strings = list(map(lambda x: str(x), images_paths))
        dataset_info = self.create_dataset(dataset_name, StorageLocation.CORD_STORAGE)

        dataset_hash = dataset_info.dataset_hash

        dataset = self.get_dataset(
            dataset_hash,
        )
        querier = dataset._client._querier

        successful_uploads = upload_to_signed_url_list(
            file_path_strings, self.user_config, querier, Images, CloudUploadSettings()
        )
        if len(images_paths) != len(successful_uploads):
            raise RuntimeError("Could not upload all the images successfully. Aborting CVAT upload.")

        upload_images_to_encord(successful_uploads, querier)

        image_title_to_image_hash_map = {}
        for image_path, successful_upload in zip(images_paths, successful_uploads):
            trimmed_image_path_str = str(image_path.relative_to(used_base_path))
            image_title_to_image_hash_map[trimmed_image_path_str] = successful_upload.data_hash

        return dataset_hash, image_title_to_image_hash_map

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self.querier.get_multiple(CloudIntegration)

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
        data = self.querier.get_multiple(OntologyWithUserRole, payload={"filter": properties_filter})
        retval: List[Dict] = []
        for row in data:
            ontology = OrmOntology.from_dict(row.ontology)
            config = SshConfig(self.user_config, resource_type=TYPE_ONTOLOGY, resource_id=ontology.ontology_hash)
            querier = Querier(config)
            retval.append(
                {
                    "ontology": Ontology(querier, config, ontology),
                    "user_role": OntologyUserRole(row.user_role),
                }
            )
        return retval

    def create_ontology(self, title: str, description: str = "", structure: OntologyStructure = None) -> Ontology:
        structure_dict = structure.to_dict() if structure else dict()
        ontology = {
            "title": title,
            "description": description,
            "editor": structure_dict,
        }

        retval = self.querier.basic_setter(OrmOntology, uid=None, payload=ontology)
        ontology = OrmOntology.from_dict(retval)
        config = SshConfig(self.user_config, resource_type=TYPE_ONTOLOGY, resource_id=ontology.ontology_hash)
        querier = Querier(config)

        return Ontology(querier, config, ontology)

    def __validate_filter(self, properties_filter: Dict) -> Dict:
        if not isinstance(properties_filter, dict):
            raise ValueError("Filter should be a dictionary")

        valid_filters = set([f.value for f in ListingFilter])

        ret = dict()

        # be relaxed with what we receive: translate raw strings to enum values
        for (clause, val) in properties_filter.items():
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
                    val = dateutil.parser.isoparse(val)
                if isinstance(val, datetime.datetime):
                    val = val.isoformat()
                else:
                    raise ValueError(f"Value for {clause.name} filter should be a datetime")

            ret[clause.value] = val

        return ret

    def deidentify_dicom_files(
        self,
        dicom_urls: List[str],
        integration_hash: str,
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
        Returns:
            Function returns list of links pointing to deidentified DICOM files,
            those will be saved to the same bucket and the same directory
            as original files with prefix ( deid_{timestamp}_ ).
            Example output:
            `[ "https://s3.region-code.amazonaws.com/bucket-name/deid_167294769118005312_dicom-file-input.dcm" ]`

        """

        return self.querier.basic_setter(
            DicomDeidentifyTask,
            uid=integration_hash,
            payload={
                "dicom_urls": dicom_urls,
            },
        )


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


CordUserClient = EncordUserClient
