import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple, Union

from encord.client import EncordClientProject
from encord.constants.model import AutomationModels, Device
from encord.http.bundle import Bundle
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.objects import LabelRowV2, OntologyStructure
from encord.ontology import Ontology
from encord.orm.analytics import (
    CollaboratorTimer,
    CollaboratorTimerParams,
    CollaboratorTimersGroupBy,
)
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import Image, Video
from encord.orm.label_log import LabelLog
from encord.orm.label_row import (
    AnnotationTaskStatus,
    LabelRow,
    LabelRowMetadata,
    LabelStatus,
    ShadowDataState,
)
from encord.orm.model import ModelConfiguration, ModelTrainingWeights, TrainingMetadata
from encord.orm.project import CopyDatasetOptions, CopyLabelsOptions
from encord.orm.project import Project as OrmProject
from encord.project_ontology.classification_type import ClassificationType
from encord.project_ontology.object_type import ObjectShape
from encord.project_ontology.ontology import Ontology as LegacyOntology
from encord.utilities.project_user import ProjectUser, ProjectUserRole


class Project:
    """
    Access project related data and manipulate the project.
    """

    def __init__(
        self, client: EncordClientProject, project_instance: OrmProject, ontology: Ontology, client_v2: ApiClient
    ):
        self._client = client
        self._client_v2 = client_v2
        self._project_instance = project_instance
        self._ontology = ontology

    @property
    def project_hash(self) -> str:
        """
        Get the project hash (i.e. the Project ID).
        """
        project_instance = self._get_project_instance()
        return project_instance.project_hash

    @property
    def title(self) -> str:
        """
        Get the title of the project.
        """
        project_instance = self._get_project_instance()
        return project_instance.title

    @property
    def description(self) -> str:
        """
        Get the description of the project.
        """
        project_instance = self._get_project_instance()
        return project_instance.description

    @property
    def created_at(self) -> datetime.datetime:
        """
        Get the time the project was created at.
        """
        project_instance = self._get_project_instance()
        return project_instance.created_at

    @property
    def last_edited_at(self) -> datetime.datetime:
        """
        Get the time the project was last edited at.
        """
        project_instance = self._get_project_instance()
        return project_instance.last_edited_at

    @property
    def ontology(self) -> dict:
        """
        Get the ontology of the project.

        DEPRECATED: Prefer using the :meth:`encord.Project.ontology_structure` method.
        """
        project_instance = self._get_project_instance()
        return project_instance.editor_ontology

    @property
    def ontology_hash(self) -> str:
        """
        Get the ontology hash of the project's ontology.
        """
        return self._ontology.ontology_hash

    @property
    def ontology_structure(self) -> OntologyStructure:
        """
        Get the ontology structure of the project's ontology.
        """
        return self._ontology.structure

    @property
    def datasets(self) -> list:
        """
        Get the associated datasets.

        Prefer using the :meth:`encord.objects.project.ProjectDataset` class to work with the data.

        .. code::

            from encord.objects.project import ProjectDataset

            project = user_client.get_project("<project_hash>")

            project_datasets = ProjectDataset.from_list(project.datasets)

        """
        project_instance = self._get_project_instance()
        return project_instance.datasets

    @property
    def label_rows(self) -> dict:
        """
        Get the label rows.
        DEPRECATED: Prefer using :meth:`list_label_row_v2()` method and :meth:`LabelRowV2` class to work with the data.

        .. code::

            from encord.orm.label_row import LabelRowMetadata

            project = user_client.get_project("<project_hash>")

            label_rows = LabelRowMetadata.from_list(project.label_rows)

        """
        project_instance = self._get_project_instance()
        if project_instance.label_rows is None:
            project_descriptor = self._client.get_project(include_labels_metadata=True)
            project_instance.label_rows = project_descriptor.label_rows

        return project_instance.label_rows

    def refetch_data(self) -> None:
        """
        The Project class will only fetch its properties once. Use this function if you suspect the state of those
        properties to be dirty.
        """
        self._project_instance = self.get_project()

    def refetch_ontology(self) -> None:
        """
        Update the ontology for the project to reflect changes on the backend
        """
        self._ontology.refetch_data()

    def get_project(self) -> OrmProject:
        """
        This function is exposed for convenience. You are encouraged to use the property accessors instead.
        """
        return self._client.get_project()

    def list_label_rows_v2(
        self,
        data_hashes: Optional[List[str]] = None,
        label_hashes: Optional[List[str]] = None,
        edited_before: Optional[Union[str, datetime.datetime]] = None,
        edited_after: Optional[Union[str, datetime.datetime]] = None,
        label_statuses: Optional[List[AnnotationTaskStatus]] = None,
        shadow_data_state: Optional[ShadowDataState] = None,
        data_title_eq: Optional[str] = None,
        data_title_like: Optional[str] = None,
        workflow_graph_node_title_eq: Optional[str] = None,
        workflow_graph_node_title_like: Optional[str] = None,
    ) -> List[LabelRowV2]:
        """
        Args:
            data_hashes: List of data hashes to filter by.
            label_hashes: List of label hashes to filter by.
            edited_before: Optionally filter to only rows last edited before the specified time
            edited_after: Optionally filter to only rows last edited after the specified time
            label_statuses: Optionally filter to only those label rows that have one of the specified :class:`~encord.orm.label_row.AnnotationTaskStatus`es
            shadow_data_state: On Optionally filter by data type in Benchmark QA projects. See :class:`~encord.orm.label_row.ShadowDataState`
            data_title_eq: Optionally filter by exact title match
            data_title_like: Optionally filter by fuzzy title match; SQL syntax
            workflow_graph_node_title_eq: Optionally filter by exact match with workflow node title
            workflow_graph_node_title_like: Optionally filter by fuzzy match with workflow node title; SQL syntax

        Returns:
            A list of :class:`~encord.objects.LabelRowV2` instances for all the matching label rows
        """
        label_row_metadatas = self._client.list_label_rows(
            edited_before,
            edited_after,
            label_statuses,
            shadow_data_state,
            data_hashes=data_hashes,
            label_hashes=label_hashes,
            include_uninitialised_labels=True,
            data_title_eq=data_title_eq,
            data_title_like=data_title_like,
            workflow_graph_node_title_eq=workflow_graph_node_title_eq,
            workflow_graph_node_title_like=workflow_graph_node_title_like,
        )

        label_rows = [
            LabelRowV2(label_row_metadata, self._client, self._ontology)  # type: ignore
            for label_row_metadata in label_row_metadatas
        ]
        return label_rows

    def add_users(self, user_emails: List[str], user_role: ProjectUserRole) -> List[ProjectUser]:
        """
        Add users to project

        Args:
            user_emails: list of user emails to be added
            user_role: the user role to assign to all users

        Returns:
            ProjectUser

        Raises:
            AuthorisationError: If the project API key is invalid.
            ResourceNotFoundError: If no project exists by the specified project EntityId.
            UnknownError: If an error occurs while adding the users to the project
        """
        return self._client.add_users(user_emails, user_role)

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
        Copy the current project into a new one with copied contents including settings, datasets and users.
        Labels and models are optional.

        Args:
            copy_datasets: if True, the datasets of the existing project are copied over, and new
                           tasks are created from those datasets
            copy_collaborators: if True, all users of the existing project are copied over with their current roles.
                                If label and/or annotator reviewer mapping is set, this will also be copied over
            copy_models: currently if True, all models with their training information will be copied into the new
                         project
            copy_labels: options for copying labels, defined in `CopyLabelsOptions`
            new_title: when provided, will be used as the title for the new project.
            new_description: when provided, will be used as the title for the new project.

        Returns:
            the EntityId of the newly created project

        Raises:
            AuthorisationError: If the project API key is invalid.
            ResourceNotFoundError: If no project exists by the specified project EntityId.
            UnknownError: If an error occurs while copying the project.
        """
        return self._client.copy_project(
            new_title=new_title,
            new_description=new_description,
            copy_datasets=copy_datasets,
            copy_collaborators=copy_collaborators,
            copy_models=copy_models,
            copy_labels=copy_labels,
        )

    def submit_label_row_for_review(self, uid: str):
        """
        Submit a label row for review.

        **Note:** this method is not supported for the workflow-based projects. See the documentation about the workflows

        Args:
            uid: A label_hash (uid) string.

        Returns:
            Bool.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while submitting for review.
            OperationNotAllowed: If the write operation is not allowed by the API key.
        """
        return self._client.submit_label_row_for_review(uid)

    def add_datasets(self, dataset_hashes: List[str]) -> bool:
        """
        Add a dataset to a project

        Args:
            dataset_hashes: List of dataset hashes of the datasets to be added

        Returns:
            Bool.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If one or more datasets don't exist by the specified dataset_hashes.
            UnknownError: If an error occurs while adding the datasets to the project.
            OperationNotAllowed: If the write operation is not allowed by the API key.
        """
        res = self._client.add_datasets(dataset_hashes)
        self._invalidate_project_instance()
        return res

    def remove_datasets(self, dataset_hashes: List[str]) -> bool:
        """
        Remove datasets from project

        Args:
            dataset_hashes: List of dataset hashes of the datasets to be removed

        Returns:
            Bool.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no dataset exists by the specified dataset_hash (uid).
            UnknownError: If an error occurs while removing the datasets from the project.
            OperationNotAllowed: If the operation is not allowed by the API key.
        """
        res = self._client.remove_datasets(dataset_hashes)
        self._invalidate_project_instance()
        return res

    def get_project_ontology(self) -> LegacyOntology:
        """
        DEPRECATED - prefer using the `ontology` property accessor instead.
        """
        return self._client.get_project_ontology()

    def add_object(self, name: str, shape: ObjectShape) -> bool:
        """
        Add object to an ontology.

        ATTENTION: this legacy method will affect all the projects sharing the same ontology

        Args:
            name: the name of the object
            shape: the shape of the object. (BOUNDING_BOX, POLYGON, POLYLINE or KEY_POINT)

        Returns:
            True if the object was added successfully and False otherwise.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while add te object to the project ontology
            OperationNotAllowed: If the operation is not allowed by the API key.
            ValueError: If invalid arguments are supplied in the function call
        """
        res = self._client.add_object(name, shape)
        self._invalidate_project_instance()
        return res

    def add_classification(
        self,
        name: str,
        classification_type: ClassificationType,
        required: bool,
        options: Optional[Iterable[str]] = None,
    ):
        """
        Add classification to an ontology.

        ATTENTION: this legacy method will affect all the projects sharing the same ontology

        Args:
            name: the name of the classification
            classification_type: the classification type (RADIO, TEXT or CHECKLIST)
            required (whether this classification is required by the annotator):
            options: the list of options for the classification (to be set to None for texts)

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while add te classification to the project ontology
            OperationNotAllowed: If the operation is not allowed by the API key.
            ValueError: If invalid arguments are supplied in the function call
        """
        res = self._client.add_classification(name, classification_type, required, options)
        self._invalidate_project_instance()
        return res

    def list_models(self) -> List[ModelConfiguration]:
        """
        List all models that are associated with the project. Use the
        :meth:`encord.project.Project.get_training_metadata` to get more metadata about each training instance.

        .. code::

            from encord.utilities.project_utilities import get_all_model_iteration_uids

            project = client_instance.get_project(<project_hash>)

            model_configurations = project.list_models()
            all_model_iteration_uids = get_all_model_iteration_uids(model_configurations)
            training_metadata = project.get_training_metadata(
                all_model_iteration_uids,
                get_model_training_labels=True,
            )
        """
        return self._client.list_models()

    def get_training_metadata(
        self,
        model_iteration_uids: Iterable[str],
        get_created_at: bool = False,
        get_training_final_loss: bool = False,
        get_model_training_labels: bool = False,
    ) -> List[TrainingMetadata]:
        """
        Given a list of model_iteration_uids, get some metadata around each model_iteration.

        Args:
            model_iteration_uids: The model iteration uids
            get_created_at: Whether the `created_at` field should be retrieved.
            get_training_final_loss: Whether the `training_final_loss` field should be retrieved.
            get_model_training_labels: Whether the `model_training_labels` field should be retrieved.
        """
        return self._client.get_training_metadata(
            model_iteration_uids, get_created_at, get_training_final_loss, get_model_training_labels
        )

    def create_model_row(
        self,
        title: str,
        description: str,
        features: List[str],
        model: Union[AutomationModels, str],
    ) -> str:
        """
        Create a model row.

        Args:
            title: Model title.
            description: Model description.
            features: List of <feature_node_hashes> which is id's of ontology objects
                      or classifications to be included in the model.
            model: the model type to be used.
                   For backwards compatibility purposes, we continuously allow strings
                   corresponding to the values of the :class:`.AutomationModels` Enum.

        Returns:
            The uid of the added model row.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ModelFeaturesInconsistentError: If a feature type is different than what is supported by the model (e.g. if
                creating a classification model using a bounding box).
        """
        return self._client.create_model_row(title, description, features, model)

    def model_delete(self, uid: str) -> bool:
        """
        Delete a model created on the platform.

        Args:
            uid: A model_hash (uid) string.

        Returns:
            bool

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no model exists by the specified model_hash (uid).
            UnknownError: If an error occurs during training.
        """

        return self._client.model_delete(uid)

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
        Run inference with model trained on the platform.

        The image(s)/video(s) can be provided either as local file paths, base64 strings, or as data hashes if the
        data is already uploaded on the Encord platform.

        Args:
            uid: A model_iteration_hash (uid) string.
            file_paths: List of local file paths to image(s) or video(s) - if running inference on files.
            base64_strings: List of base 64 strings of image(s) or video(s) - if running inference on base64 strings.
            conf_thresh: Confidence threshold (default 0.6).
            iou_thresh: Intersection over union threshold (default 0.3).
            device: Device (CPU or CUDA, default is CUDA).
            detection_frame_range: Detection frame range (for videos).
            allocation_enabled: Object UID allocation (tracking) enabled (disabled by default).
            data_hashes: list of hash of the videos/image_groups you'd like to run inference on.
            rdp_thresh: parameter specifying the polygon coarseness to be used while running inference. The higher the
                value, the less points in the segmented image

        Returns:
            Inference results: A dict of inference results.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no model exists by the specified model_iteration_hash (uid).
            UnknownError: If an error occurs while running inference.
            FileTypeNotSupportedError: If the file type is not supported for inference (has to be an image or video)
            FileSizeNotSupportedError: If the file size is too big to be supported.
            DetectionRangeInvalidError: If a detection range is invalid for video inference
        """
        return self._client.model_inference(
            uid,
            file_paths,
            base64_strings,
            conf_thresh,
            iou_thresh,
            device,
            detection_frame_range,
            allocation_enabled,
            data_hashes,
            rdp_thresh,
        )

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
        Train a model created on the platform.

        Args:
            uid: A model_hash (uid) string.
            label_rows: List of label row uid's (hashes) for training.
            epochs: Number of passes through training dataset.
            batch_size: Number of training examples utilized in one iteration.
            weights: Model weights.
            device: Device (CPU or CUDA, default is CUDA).

        Returns:
            A model iteration object.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ModelWeightsInconsistentError: If the passed model weights are incompatible with the selected model.
            ResourceNotFoundError: If no model exists by the specified model_hash (uid).
            UnknownError: If an error occurs during training.
        """
        return self._client.model_train(
            uid,
            label_rows,
            epochs,
            batch_size,
            weights,
            device,
        )

    def object_interpolation(
        self,
        key_frames,
        objects_to_interpolate,
    ):
        """
        Run object interpolation algorithm on project labels (requires an editor ontology and feature uid's).

        Interpolation is supported for bounding box, polygon, and keypoint.

        Args:
            key_frames: Labels for frames to be interpolated. Key frames are consumed in the form::

                {
                    "<frame_number>": {
                        "objects": [
                            {
                                "objectHash": "<object_hash>",
                                "featureHash": "<feature_hash>",
                                "polygon": {
                                    "0": { "x": x1, "y": y1, },
                                    "1": { "x": x2, "y": y2, },
                                    # ...,
                                }
                            },
                            # ...
                        ]
                    },
                    # ...,
                }

            objects_to_interpolate: List of object uid's (hashes) of objects to interpolate.

        Returns:
            Interpolation results: Full set of filled frames including interpolated objects.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while running interpolation.
        """
        return self._client.object_interpolation(key_frames, objects_to_interpolate)

    def fitted_bounding_boxes(
        self,
        frames: dict,
        video: dict,
    ):
        """

        Args:
            frames: Labels for frames to be fitted. Frames are consumed in the form::

                {
                    "<frame_number>": {
                        "objects": [
                            {
                                "objectHash": "<object_hash>",
                                "featureHash": "<feature_hash>",
                                "polygon": {
                                    "0": { "x": x1, "y": y1, },
                                    "1": { "x": x2, "y": y2, },
                                    # ...,
                                }
                            },
                            # ...
                        ]
                    },
                    # ...,
                }

            video: Metadata of the video for which bounding box fitting needs to be
                   run::

                        {
                            "width" : w,
                            "height" : h,
                        }

        Returns:
            Fitting results: Full set of filled frames including fitted objects.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while running interpolation.
        """
        return self._client.fitted_bounding_boxes(frames, video)

    def get_data(self, data_hash: str, get_signed_url: bool = False) -> Tuple[Optional[Video], Optional[List[Image]]]:
        """
        Retrieve information about a video or image group.

        Args:
            data_hash: The uid of the data object
            get_signed_url: Optionally return signed URLs for timed public access to that resource
                (default False)

        Returns:
            A consisting of the video (if it exists) and a list of individual images (if they exist)

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while retrieving the object.
        """
        return self._client.get_data(data_hash, get_signed_url)

    def get_websocket_url(self) -> str:
        return self._client.get_websocket_url()

    def get_label_logs(
        self,
        user_hash: Optional[str] = None,
        data_hash: Optional[str] = None,
        from_unix_seconds: Optional[int] = None,
        to_unix_seconds: Optional[int] = None,
    ) -> List[LabelLog]:
        """
        Get label logs, which represent the actions taken in the UI to create labels.

        All arguments can be left as `None` if no filtering should be applied.

        Args:
            user_hash: Filter the label logs by the user.
            data_hash: Filter the label logs by the data_hash.
            from_unix_seconds: Filter the label logs to only include labels after this timestamp.
            from_unix_seconds: Filter the label logs to only include labels before this timestamp.
        """
        return self._client.get_label_logs(user_hash, data_hash, from_unix_seconds, to_unix_seconds)

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self._client.get_cloud_integrations()

    def list_label_rows(
        self,
        edited_before: Optional[Union[str, datetime.datetime]] = None,
        edited_after: Optional[Union[str, datetime.datetime]] = None,
        label_statuses: Optional[List[AnnotationTaskStatus]] = None,
        shadow_data_state: Optional[ShadowDataState] = None,
        *,
        include_uninitialised_labels=False,
        label_hashes: Optional[List[str]] = None,
        data_hashes: Optional[List[str]] = None,
    ) -> List[LabelRowMetadata]:
        """
        DEPRECATED - use `list_label_rows_v2` to manage label rows instead.

        Args:
            edited_before: Optionally filter to only rows last edited before the specified time
            edited_after: Optionally filter to only rows last edited after the specified time
            label_statuses: Optionally filter to only those label rows that have one of the specified :class:`~encord.orm.label_row.AnnotationTaskStatus`
            shadow_data_state: On Optionally filter by data type in Benchmark QA projects. See :class:`~encord.orm.label_row.ShadowDataState`
            include_uninitialised_labels: Whether to return only label rows that are "created" and have a label_hash
                (default). If set to `True`, this will return all label rows, including those that do not have a
                label_hash.
            data_hashes: List of data hashes to filter by.
            label_hashes: List of label hashes to filter by.

        Returns:
            A list of :class:`~encord.orm.label_row.LabelRowMetadata` instances for all the matching label rows

        Raises:
            UnknownError: If an error occurs while retrieving the data.
        """
        return self._client.list_label_rows(
            edited_before,
            edited_after,
            label_statuses,
            shadow_data_state,
            include_uninitialised_labels=include_uninitialised_labels,
            label_hashes=label_hashes,
            data_hashes=data_hashes,
        )

    def set_label_status(self, label_hash: str, label_status: LabelStatus) -> bool:
        """
        DEPRECATED - this function is currently not maintained.

        Set the label status for a label row to a desired value.

        Args:
            self: Encord client object.
            label_hash: unique identifier of the label row whose status is to be updated.
            label_status: the new status that needs to be set.

        Returns:
            Bool.

        Raises:
            AuthorisationError: If the label_hash provided is invalid or not a member of the project.
            UnknownError: If an error occurs while updating the status.
        """
        return self._client.set_label_status(label_hash, label_status)

    def get_label_row(
        self,
        uid: str,
        get_signed_url: bool = True,
        *,
        include_object_feature_hashes: Optional[Set[str]] = None,
        include_classification_feature_hashes: Optional[Set[str]] = None,
        include_reviews: bool = False,
    ) -> LabelRow:
        """
        DEPRECATED: Prefer using the list_label_rows_v2 function to interact with label rows.

        Retrieve label row. If you need to retrieve multiple label rows, prefer using
        :meth:`encord.project.Project.get_label_rows` instead.

        A code example using the `include_object_feature_hashes` and `include_classification_feature_hashes`
        filters can be found in :meth:`encord.project.Project.get_label_row`.


        Args:
            uid: A label_hash   (uid) string.
            get_signed_url: Whether to generate signed urls to the data asset. Generating these should be disabled
                if the signed urls are not used to speed up the request.
            include_object_feature_hashes: If None all the objects will be included. Otherwise, only objects labels
                will be included of which the feature_hash has been added.
            include_classification_feature_hashes: If None all the classifications will be included. Otherwise, only
                classification labels will be included of which the feature_hash has been added.
            include_reviews: Whether to request read only information about the reviews of the label row.

        Returns:
            LabelRow: A label row instance.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no label exists by the specified label_hash (uid).
            UnknownError: If an error occurs while retrieving the label.
            OperationNotAllowed: If the read operation is not allowed by the API key.
        """
        return self._client.get_label_row(
            uid,
            get_signed_url,
            include_object_feature_hashes=include_object_feature_hashes,
            include_classification_feature_hashes=include_classification_feature_hashes,
            include_reviews=include_reviews,
        )

    def get_label_rows(
        self,
        uids: List[str],
        get_signed_url: bool = True,
        *,
        include_object_feature_hashes: Optional[Set[str]] = None,
        include_classification_feature_hashes: Optional[Set[str]] = None,
        include_reviews: bool = False,
    ) -> List[LabelRow]:
        """
        DEPRECATED: Prefer using the list_label_rows_v2 function to interact with label rows.

        Retrieve a list of label rows. Duplicates will be dropped. The result will come back in a random order.

        This return is undefined behaviour if any of the uids are invalid (i.e. it may randomly fail or randomly
        succeed and should not be relied upon).

        .. code::

                # Code example of using the object filters.
                from encord.objects.common import Shape
                from encord.objects.ontology_structure import OntologyStructure

                project = ... # assuming you already have instantiated this Project object

                # Get all feature hashes of the objects which are of type `Shape.BOUNDING_BOX`
                ontology = OntologyStructure.from_dict(project.ontology)
                only_bounding_box_feature_hashes = set()
                for object_ in ontology.objects:
                    if object_.shape == Shape.BOUNDING_BOX:
                        only_bounding_box_feature_hashes.add(object_.feature_node_hash)

                no_classification_feature_hashes = set()  # deliberately left empty

                # Get all labels of tasks that have already been initiated.
                # Include only labels of bounding boxes and exclude all
                # classifications
                label_hashes = []
                for label_row in project.label_rows:
                    # Trying to run `get_label_row` on a label_row without a `label_hash` would fail.
                    if label_row["label_hash"] is not None:
                        label_hashes.append(label_row["label_hash"])

                all_labels = project.get_label_rows(
                    label_hashes,
                    include_object_feature_hashes=only_bounding_box_feature_hashes,
                    include_classification_feature_hashes=no_classification_feature_hashes,
                )

        Args:
             uids:
                A list of label_hash (uid).
             get_signed_url:
                Whether to generate signed urls to the data asset. Generating these should be disabled
                if the signed urls are not used to speed up the request.
            include_object_feature_hashes:
                If None all the objects will be included. Otherwise, only objects labels
                will be included of which the feature_hash has been added.
            include_classification_feature_hashes:
                If None all the classifications will be included. Otherwise, only
                classification labels will be included of which the feature_hash has been added.
            include_reviews: Whether to request read only information about the reviews of the label row.

        Raises:
            MultiLabelLimitError: If too many labels were requested. Check the error's `maximum_labels_allowed` field
                to read the most up to date error limit.
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no label exists by the specified label_hash (uid).
            UnknownError: If an error occurs while retrieving the label.
            OperationNotAllowed: If the read operation is not allowed by the API key.
        """
        return self._client.get_label_rows(
            uids,
            get_signed_url,
            include_object_feature_hashes=include_object_feature_hashes,
            include_classification_feature_hashes=include_classification_feature_hashes,
            include_reviews=include_reviews,
        )

    def save_label_row(self, uid, label):
        """
        DEPRECATED: Prefer using the list_label_rows_v2 function to interact with label rows.

        Save existing label row.

        If you have a series of frame labels and have not updated answer
        dictionaries, call the construct_answer_dictionaries utilities function
        to do so prior to saving labels.

        Args:
            uid: A label_hash (uid) string.
            label: A label row instance.

        Returns:
            Bool.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no label exists by the specified label_hash (uid).
            UnknownError: If an error occurs while saving the label.
            OperationNotAllowed: If the write operation is not allowed by the API key.
            AnswerDictionaryError: If an object or classification instance is missing in answer dictionaries.
            CorruptedLabelError: If a blurb is corrupted (e.g. if the frame labels have more frames than the video).
        """
        return self._client.save_label_row(uid, label)

    def create_label_row(self, uid: str):
        """
        DEPRECATED: Prefer using the list_label_rows_v2 function to interact with label rows.

        Create a label row (for data in a project not previously been labeled).

        Args:
            uid: the data_hash (uid) of the data unit being labeled.
                Available in client.get_project().get('label_rows')
                where label_status is NOT_LABELLED.

        Returns:
            LabelRow: A label row instance.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while saving the label.
            OperationNotAllowed: If the write operation is not allowed by the API key.
            AnswerDictionaryError: If an object or classification instance is missing in answer dictionaries.
            CorruptedLabelError: If a blurb is corrupted (e.g. if the frame labels have more frames than the video).
            ResourceExistsError: If a label row already exists for this project data. Avoids overriding existing work.
        """
        return self._client.create_label_row(uid)

    def _get_project_instance(self):
        if self._project_instance is None:
            self._project_instance = self.get_project()
        return self._project_instance

    def _invalidate_project_instance(self):
        self._project_instance = None

    def create_bundle(self) -> Bundle:
        """
        Initialises a bundle to reduce amount of network calls performed by the Encord SDK

        See the :class:`encord.http.bundle.Bundle` documentation for more details
        """
        return Bundle()

    def list_collaborator_timers(
        self,
        after: datetime.datetime,
        before: Optional[datetime.datetime] = None,
        group_by_data_unit: bool = True,
    ) -> Iterable[CollaboratorTimer]:
        """
        Provides information about time spent for each collaborator that has worked on the project within a specified
        range of dates.

        Args:
             after: the beginning of the period of interest.
             before: the end of period of interest.
             group_by_data_unit: if True, time spent by a collaborator for each data unit is provided separately,
                                 and if False, all time spent in the scope of the project is aggregated together.

        Returns:
            Iterable[CollaboratorTimer]
        """

        params = CollaboratorTimerParams(
            project_hash=self.project_hash,
            after=after,
            before=before,
            group_by=CollaboratorTimersGroupBy.DATA_UNIT if group_by_data_unit else CollaboratorTimersGroupBy.PROJECT,
            page_size=100,
        )

        while True:
            page = self._client_v2.get(
                Path("analytics/collaborators/timers"), params=params, result_type=Page[CollaboratorTimer]
            )

            for result in page.results:
                yield result

            if page.next_page_token is not None:
                params.page_token = page.next_page_token
            else:
                break
