import datetime
from typing import Iterable, List, Optional, Tuple, Union

from encord.client import EncordClientProject
from encord.constants.model import AutomationModels
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import Image, Video
from encord.orm.label_log import LabelLog
from encord.orm.label_row import AnnotationTaskStatus, LabelRowMetadata, LabelStatus
from encord.orm.model import ModelConfiguration, TrainingMetadata
from encord.orm.project import Project as OrmProject
from encord.project_ontology.classification_type import ClassificationType
from encord.project_ontology.object_type import ObjectShape
from encord.project_ontology.ontology import Ontology as LegacyOntology
from encord.utilities.project_user import ProjectUser, ProjectUserRole


class Project:
    """
    Access project related data and manipulate the project.
    """

    def __init__(self, client: EncordClientProject):
        self._client = client
        self._project_instance: Optional[OrmProject] = None

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

        BETA: Prefer using the :class:`encord.objects.ontology_structure.OntologyStructure` class to work with the data.

        .. code::

            from encord.object.ontology_structure import OntologyStructure

            project = user_client.get_project("<project_hash>")

            ontology = OntologyStructure.from_dict(project.ontology)

        """
        project_instance = self._get_project_instance()
        return project_instance.editor_ontology

    @property
    def datasets(self) -> list:
        """
        Get the associated datasets.

        Prefer using the :meth:`encord.objects.project.ProjectDataset` class to work with the data.

        .. code::

            from encord.object.project import ProjectDataset

            project = user_client.get_project("<project_hash>")

            project_datasets = ProjectDataset.from_list(project.datasets)

        """
        project_instance = self._get_project_instance()
        return project_instance.datasets

    @property
    def label_rows(self) -> dict:
        """
        Get the label rows.

        Prefer using the :meth:`encord.orm.label_row.LabelRowMetadata` class to work with the data.

        .. code::

            from encord.orm.label_row import LabelRowMetadata

            project = user_client.get_project("<project_hash>")

            label_rows = LabelRowMetadata.from_list(project.label_rows)

        """
        project_instance = self._get_project_instance()
        return project_instance.label_rows

    def refetch_data(self) -> None:
        """
        The Project class will only fetch its properties once. Use this function if you suspect the state of those
        properties to be dirty.
        """
        self._project_instance = self.get_project()

    def get_project(self) -> OrmProject:
        """
        This function is exposed for convenience. You are encouraged to use the property accessors instead.
        """
        return self._client.get_project()

    def list_label_rows(
        self,
        edited_before: Optional[Union[str, datetime.datetime]] = None,
        edited_after: Optional[Union[str, datetime.datetime]] = None,
        label_statuses: Optional[List[AnnotationTaskStatus]] = None,
    ) -> List[LabelRowMetadata]:
        return self._client.list_label_rows(edited_before, edited_after, label_statuses)

    def set_label_status(self, label_hash: str, label_status: LabelStatus) -> bool:
        """
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

    def copy_project(self, copy_datasets=False, copy_collaborators=False, copy_models=False) -> str:
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

        Returns:
            the EntityId of the newly created project

        Raises:
            AuthorisationError: If the project API key is invalid.
            ResourceNotFoundError: If no project exists by the specified project EntityId.
            UnknownError: If an error occurs while copying the project.
        """
        return self._client.copy_project(copy_datasets, copy_collaborators, copy_models)

    def get_label_row(self, uid: str, get_signed_url: bool = True):
        """
        Retrieve label row.

        Args:
            uid: A label_hash   (uid) string.
            get_signed_url: By default the operation returns a signed URL for the underlying data asset. This can be
            expensive so it can optionally be turned off

        Returns:
            LabelRow: A label row instance.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no label exists by the specified label_hash (uid).
            UnknownError: If an error occurs while retrieving the label.
            OperationNotAllowed: If the read operation is not allowed by the API key.
        """
        return self._client.get_label_row(uid, get_signed_url)

    def save_label_row(self, uid, label):
        """
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

    def submit_label_row_for_review(self, uid: str):
        """
        Submit a label row for review.

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
        return self._client.add_datasets(dataset_hashes)

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
        return self._client.remove_datasets(dataset_hashes)

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
        return self._client.add_object(name, shape)

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
        return self._client.add_classification(name, classification_type, required, options)

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
        uid,
        file_paths=None,
        base64_strings=None,
        conf_thresh=0.6,
        iou_thresh=0.3,
        device="cuda",
        detection_frame_range=None,
        allocation_enabled=False,
        data_hashes=None,
        rdp_thresh=0.005,
    ):
        """
        Run inference with model trained on the platform.

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

    def model_train(self, uid, label_rows=None, epochs=None, batch_size=24, weights=None, device="cuda"):
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
        self, user_hash: str = None, data_hash: str = None, from_unix_seconds: int = None, to_unix_seconds: int = None
    ) -> List[LabelLog]:
        return self._client.get_label_logs(user_hash, data_hash, from_unix_seconds, to_unix_seconds)

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self._client.get_cloud_integrations()

    def _get_project_instance(self):
        if self._project_instance is None:
            self._project_instance = self.get_project()
        return self._project_instance
