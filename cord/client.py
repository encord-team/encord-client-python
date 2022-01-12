#
# Copyright (c) 2020 Cord Technologies Limited
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

""" ``cord.client`` provides a simple Python client that allows you
to query project resources through the Cord API.

Here is a simple example for instantiating the client for a project
and obtaining project info:

.. test_blurb2.py code::

    from cord.client import CordClient

    client = CordClient.initialize('YourProjectID', 'YourAPIKey')
    client.get_project()

    Returns:
        Project: A project record instance. See Project ORM for details.

"""

from __future__ import annotations

import base64
import json
import logging
import os.path
import typing
import uuid
from pathlib import Path
from typing import List, Tuple, Union, Optional

import cord.exceptions
from cord.configs import CordConfig, Config, CORD_DOMAIN
from cord.constants.model import *
from cord.constants.string_constants import *
from cord.http.querier import Querier
from cord.http.utils import upload_to_signed_url_list
from cord.orm.api_key import ApiKeyMeta
from cord.orm.cloud_integration import CloudIntegration
from cord.orm.dataset import (
    Dataset,
    Image,
    ImageGroup,
    SignedImagesURL,
    SignedVideoURL,
    Video,
    DatasetData,
    ReEncodeVideoTask,
    ImageGroupOCR,
)
from cord.orm.label_log import LabelLog
from cord.orm.label_row import LabelRow
from cord.orm.labeling_algorithm import LabelingAlgorithm, ObjectInterpolationParams, BoundingBoxFittingParams
from cord.orm.model import Model, ModelRow, ModelInferenceParams, ModelTrainingParams, ModelOperations
from cord.orm.project import Project, ProjectCopy, ProjectDataset, ProjectUsers, ProjectCopyOptions
from cord.project_ontology.classification_type import ClassificationType
from cord.project_ontology.object_type import ObjectShape
from cord.project_ontology.ontology import Ontology
from cord.utilities.project_user import ProjectUserRole, ProjectUser

logger = logging.getLogger(__name__)


class CordClient(object):
    """
    Cord client. Allows you to query db items associated
    with a project (e.g. label rows, datasets).
    """

    def __init__(self, querier: Querier, config: Config):
        self._querier = querier
        self._config: Config = config

    @staticmethod
    def initialise(
        resource_id: Optional[str] = None, api_key: Optional[str] = None, domain: str = CORD_DOMAIN
    ) -> Union[CordClientProject, CordClientDataset]:
        """
        Create and initialize a Cord client from a resource EntityId and API key.

        Args:
            resource_id: either of
                - A project EntityId string.
                  If None, uses the CORD_PROJECT_ID environment variable.
                - A dataset EntityId string.
                  If None, uses the CORD_DATASET_ID environment variable.
            api_key: An API key.
                     If None, uses the CORD_API_KEY environment variable.
            domain: The cord api-server domain.
                If None, the CORD_DOMAIN is used

        Returns:
            CordClient: A Cord client instance.
        """
        config = CordConfig(resource_id, api_key, domain=domain)
        return CordClient.initialise_with_config(config)

    @staticmethod
    def initialise_with_config(config: Config) -> Union[CordClientProject, CordClientDataset]:
        """
        Create and initialize a Cord client from a Cord config instance.

        Args:
            config: A Cord config instance.

        Returns:
            CordClient: A Cord client instance.
        """
        querier = Querier(config)
        key_type = querier.basic_getter(ApiKeyMeta)
        resource_type = key_type.get("resource_type", None)

        if resource_type == TYPE_PROJECT:
            logger.info("Initialising Cord client for project using key: %s", key_type.get("title", ""))
            return CordClientProject(querier, config)

        elif resource_type == TYPE_DATASET:
            logger.info("Initialising Cord client for dataset using key: %s", key_type.get("title", ""))
            return CordClientDataset(querier, config)

        else:
            raise cord.exceptions.InitialisationError(
                message=f"API key [{config.api_key}] is not associated with a project or dataset"
            )

    def __getattr__(self, name):
        """Overriding __getattr__."""
        value = self.__dict__.get(name)
        if not value:
            self_type = type(self).__name__
            if self_type == "CordClientDataset" and name in CordClientProject.__dict__.keys():
                raise cord.exceptions.CordException(
                    message=("{} is implemented in Projects, not Datasets.".format(name))
                )
            elif self_type == "CordClientProject" and name in CordClientDataset.__dict__.keys():
                raise cord.exceptions.CordException(
                    message=("{} is implemented in Datasets, not Projects.".format(name))
                )
            elif name == "items":
                pass
            else:
                raise cord.exceptions.CordException(message="{} is not implemented.".format(name))
        return value

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self._querier.get_multiple(CloudIntegration)


class CordClientDataset(CordClient):
    def get_dataset(self) -> Dataset:
        """
        Retrieve dataset info (pointers to data, labels).

        Args:
            self: Cord client object.

        Returns:
            Dataset: A dataset record instance.

        Raises:
            AuthorisationError: If the dataset API key is invalid.
            ResourceNotFoundError: If no dataset exists by the specified dataset EntityId.
            UnknownError: If an error occurs while retrieving the dataset.
        """
        return self._querier.basic_getter(Dataset)

    def upload_video(self, file_path: str):
        """
        Upload video to Cord storage.

        Args:
            self: Cord client object.
            file_path: path to video e.g. '/home/user/data/video.mp4'

        Returns:
            Bool.

        Raises:
            UploadOperationNotSupportedError: If trying to upload to external
                                              datasets (e.g. S3/GPC/Azure)
        """
        if os.path.exists(file_path):
            short_name = os.path.basename(file_path)
            signed_url = self._querier.basic_getter(SignedVideoURL, uid=short_name)
            res = upload_to_signed_url_list([file_path], [signed_url], self._querier, Video)
            if res:
                logger.info("Upload complete.")
                logger.info("Please run client.get_dataset() to refresh.")
                return res
            else:
                raise cord.exceptions.CordException(message="An error has occurred during video upload.")
        else:
            raise cord.exceptions.CordException(message="{} does not point to a file.".format(file_path))

    def create_image_group(self, file_paths: typing.Iterable[str], max_workers: Optional[int] = None):
        """
        Create an image group in Cord storage.

        Args:
            self: Cord client object.
            file_paths: a list of paths to images, e.g.
                ['/home/user/data/img1.png', '/home/user/data/img2.png']
            max_workers:
                Number of workers for parallel image upload. If set to None, this will be the number of CPU cores
                available on the machine.

        Returns:
            Bool.

        Raises:
            UploadOperationNotSupportedError: If trying to upload to external
                                              datasets (e.g. S3/GPC/Azure)
        """
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise cord.exceptions.CordException(message="{} does not point to a file.".format(file_path))
        short_names = list(map(os.path.basename, file_paths))
        signed_urls = self._querier.basic_getter(SignedImagesURL, uid=short_names)
        upload_to_signed_url_list(file_paths, signed_urls, self._querier, Image, max_workers)
        image_hash_list = list(map(lambda signed_url: signed_url.get("data_hash"), signed_urls))
        res = self._querier.basic_setter(ImageGroup, uid=image_hash_list, payload={})
        if res:
            titles = [video_data.get("title") for video_data in res]
            logger.info("Upload successful! {} created.".format(titles))
            logger.info("Please run client.get_dataset() to refresh.")
            return res
        else:
            raise cord.exceptions.CordException(message="An error has occurred during image group creation.")

    def delete_image_group(self, data_hash: str):
        """
        Create an image group in Cord storage.

        Args:
            self: Cord client object.
            data_hash: the hash of the image group you'd like to delete
        """
        self._querier.basic_delete(ImageGroup, uid=data_hash)

    def delete_data(self, data_hashes: List[str]):
        """
        Delete a video/image group from a dataset.

        Args:
            self: Cord client object.
            data_hashes: list of hash of the videos/image_groups you'd like to delete, all should belong to the same
             dataset
        """
        self._querier.basic_delete(Video, uid=data_hashes)

    def add_private_data_to_dataset(
        self,
        integration_id: str,
        private_files: Union[str, typing.Dict, Path, typing.TextIO],
        ignore_errors: bool = False,
    ):
        """
        Append data hosted on private clouds to existing dataset

        Args:
            integration_id: str
                EntityId of the cloud integration to be used when accessing those files
            private_files:
                A str path or Path object to a json file, json str or python dictionary of the files you wish to add
            ignore_errors: bool, optional
                Ignore individual errors when trying to access the specified files
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

        self._querier.basic_setter(DatasetData, self._config.resource_id, payload=payload)

    def re_encode_data(self, data_hashes: List[str]):
        """
        Launches an async task that can re-encode a list of videos.

        Args:
            self: Cord client object.
            data_hashes: list of hash of the videos you'd like to re_encode, all should belong to the same
             dataset
        Returns:
            EntityId(integer) of the async task launched.

        """
        payload = {"data_hash": data_hashes}
        return self._querier.basic_put(ReEncodeVideoTask, uid=None, payload=payload)

    def re_encode_data_status(self, job_id: int):
        """
        Returns the status of an existing async task which is aimed at re-encoding videos.

        Args:
            self: Cord client object.
            job_id: id of the async task that was launched to re-encode the videos

        Returns:
            ReEncodeVideoTask: Object containing the status of the task, along with info about the new encoded videos
             in case the task has been completed
        """
        return self._querier.basic_getter(ReEncodeVideoTask, uid=job_id)

    def run_ocr(self, image_group_id: str) -> List[ImageGroupOCR]:
        """
        Returns an optical character recognition result for a given image group
        Args:
            image_group_id: the id of the image group in this dataset to run OCR on

        Returns:
            Returns a list of ImageGroupOCR objects representing the text and corresponding coordinates
            found in each frame of the image group
        """

        payload = {"image_group_data_hash": image_group_id}

        response = self._querier.get_multiple(ImageGroupOCR, payload=payload)

        return response


class CordClientProject(CordClient):
    def get_project(self):
        """
        Retrieve project info (pointers to data, labels).

        Args:
            self: Cord client object.

        Returns:
            Project: A project record instance.

        Raises:
            AuthorisationError: If the project API key is invalid.
            ResourceNotFoundError: If no project exists by the specified project EntityId.
            UnknownError: If an error occurs while retrieving the project.
        """
        return self._querier.basic_getter(Project)

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

        payload = {"user_emails": user_emails, "user_role": user_role}

        users = self._querier.basic_setter(ProjectUsers, self._config.resource_id, payload=payload)

        return list(map(lambda user: ProjectUser.from_dict(user), users))

    def copy_project(self, copy_datasets=False, copy_collaborators=False, copy_models=False):
        """
        Copy the current project into a new one with copied contents including settings, datasets and users.
        Labels and models are optional
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

        payload = {"copy_project_options": []}
        if copy_datasets:
            payload["copy_project_options"].append(ProjectCopyOptions.DATASETS.value)
        if copy_models:
            payload["copy_project_options"].append(ProjectCopyOptions.MODELS.value)
        if copy_collaborators:
            payload["copy_project_options"].append(ProjectCopyOptions.COLLABORATORS.value)

        return self._querier.basic_setter(ProjectCopy, self._config.resource_id, payload=payload)

    def get_label_row(self, uid: str, get_signed_url: bool = True):
        """
        Retrieve label row.

        Args:
            uid: A label_hash (uid) string.
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
        payload = {"get_signed_url": get_signed_url}

        return self._querier.basic_getter(LabelRow, uid, payload=payload)

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
        label = LabelRow(label)
        return self._querier.basic_setter(LabelRow, uid, payload=label)

    def create_label_row(self, uid):
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
        return self._querier.basic_put(LabelRow, uid=uid, payload=None)

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
        payload = {"dataset_hashes": dataset_hashes}
        return self._querier.basic_setter(ProjectDataset, uid=None, payload=payload)

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
            ResourceNotFoundError: If no dataset exists by the specified dataset_uid (uid).
            UnknownError: If an error occurs while removing the datasets from the project.
            OperationNotAllowed: If the o`peration is not allowed by the API key.
        """
        return self._querier.basic_delete(ProjectDataset, uid=dataset_hashes)

    def get_project_ontology(self) -> Ontology:
        project = self.get_project()
        ontology = project["editor_ontology"]
        return Ontology.from_dict(ontology)

    def add_object(self, name: str, shape: ObjectShape) -> bool:
        """
        Add object to an ontology
        Args:
            name: the name of the object
            shape: the shape of the object (BOUNDING_BOX, POLYGON or KEY_POINT)

        Returns:
            bool

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while add te object to the project ontology
            OperationNotAllowed: If the operation is not allowed by the API key.
            ValueError: If invalid arguments are supplied in the function call
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
        options: Optional[typing.Iterable[str]] = None,
    ):
        """

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
        if len(name) == 0:
            raise ValueError("Ontology classification name is empty")

        ontology = self.get_project_ontology()
        ontology.add_classification(name, classification_type, required, options)
        return self.__set_project_ontology(ontology)

    def create_model_row(
        self,
        title=None,
        description=None,
        features=None,
        model=None,
    ) -> str:
        """
        Create a model row.

        Args:
            title: Model title.
            description: Model description.
            features: List of feature feature uid's (hashes) to be included in the model.
            model: Model (resnet18, resnet34, resnet50,
                resnet101, resnet152, vgg16, vgg19, yolov5, faster_rcnn, mask_rcnn).

        Returns:
            The uid of the added model row.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ModelFeaturesInconsistentError: If a feature type is different than what is supported by the model (e.g. if
                creating a classification model using a bounding box).
        """
        if title is None:
            raise cord.exceptions.CordException(message="You must set a title to create a model row.")

        if features is None:
            raise cord.exceptions.CordException(
                message="You must pass a list of feature uid's (hashes) to create a model row."
            )

        if model is None or model not in [
            RESNET18,
            RESNET34,
            RESNET50,
            RESNET101,
            RESNET152,
            VGG16,
            VGG19,
            YOLOV5,
            FASTER_RCNN,
            MASK_RCNN,
        ]:
            raise cord.exceptions.CordException(
                message="You must pass a model (resnet18, resnet34, resnet50, resnet101, resnet152, vgg16, vgg19, "
                "yolov5, faster_rcnn, mask_rcnn) to create a model row."
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
        return self._querier.basic_delete(Model, uid=uid)

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

        Returns:
            Inference results: A dict of inference results.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no model exists by the specified model_iteration_hash (uid).
            UnknownError: If an error occurs while running inference.
            FileTypeNotSupportedError: If the file type is not supported for inference (has to be an image or video)
            DetectionRangeInvalidError: If a detection range is invalid for video inference
        """
        if (file_paths is None and base64_strings is None) or (
            file_paths is not None and len(file_paths) > 0 and base64_strings is not None and len(base64_strings) > 0
        ):
            raise cord.exceptions.CordException(
                message="To run model inference, you must pass either a list of files or base64 strings."
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
                "device": device,
                "detection_frame_range": detection_frame_range,
                "allocation_enabled": allocation_enabled,
            }
        )

        model = Model(
            {
                "model_operation": ModelOperations.INFERENCE.value,
                "model_parameters": inference_params,
            }
        )

        return self._querier.basic_setter(Model, uid, payload=model)

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
        if label_rows is None:
            raise cord.exceptions.CordException(
                message="You must pass a list of label row uid's (hashes) to train a model."
            )

        if epochs is None:
            raise cord.exceptions.CordException(message="You must set number of epochs to train a model.")

        if batch_size is None:
            raise cord.exceptions.CordException(message="You must set a batch size to train a model.")

        if weights is None:
            raise cord.exceptions.CordException(message="You must select model weights to train a model.")

        if device is None:
            raise cord.exceptions.CordException(message="You must set a device (cuda or CPU) train a model.")

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
        Run object interpolation algorithm on project labels (requires an editor ontology and feature uid's).

        Interpolation is supported for bounding box, polygon, and keypoint.

        Args:
            key_frames: Labels for frames to be interpolated. Key frames are consumed in the form:

                "frame": {
                    "objects": [
                        {
                            "objectHash": object_uid,
                            "featureHash": feature_uid (from editor ontology),
                            "polygon": {
                                "0": {
                                    "x": x1,
                                    "y": y1,
                                },
                                "1": {
                                    "x": x2,
                                    "y": y2,
                                },
                                "2" {
                                    "x": x3,
                                    "y": y3,
                                },
                                ...,
                            }
                        },
                        {
                            ...
                        }
                    ]
                },
                "frame": {
                    ...,
                }

            objects_to_interpolate: List of object uid's (hashes) of objects to interpolate.

        Returns:
            Interpolation results: Full set of filled frames including interpolated objects.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while running interpolation.
        """
        if len(key_frames) == 0 or len(objects_to_interpolate) == 0:
            raise cord.exceptions.CordException(
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

        Args:
            frames: Labels for frames to be fitted. Frames are consumed in the form:

                "frame": {
                    "objects": [
                        {
                            "objectHash": object_uid,
                            "featureHash": feature_uid (from editor ontology),
                            "polygon": {
                                "0": {
                                    "x": x1,
                                    "y": y1,
                                },
                                "1": {
                                    "x": x2,
                                    "y": y2,
                                },
                                "2" {
                                    "x": x3,
                                    "y": y3,
                                },
                                ...,
                            }
                        },
                        {
                            ...
                        }
                    ]
                },
                "frame": {
                    ...,
                }

            video: Metadata of the video for which bounding box fitting needs to be run

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
        if len(frames) == 0 or len(video) == 0:
            raise cord.exceptions.CordException(
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
        Retrieve information about a video or image group.

        Params:
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
        return (
            f"{self._config.websocket_endpoint}?"
            f"client_type={2}&"
            f"project_hash={self._config.resource_id}&"
            f"api_key={self._config.api_key}"
        )

    def get_label_logs(
        self, user_hash: str = None, data_hash: str = None, from_unix_seconds: int = None, to_unix_seconds: int = None
    ) -> List[LabelLog]:

        function_arguments = locals()

        query_payload = {k: v for (k, v) in function_arguments.items() if k is not "self" and v is not None}

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
        return self._querier.basic_setter(Project, uid=None, payload=payload)
