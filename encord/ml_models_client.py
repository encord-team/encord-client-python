import base64
import logging
import time
from math import ceil
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from uuid import UUID

import requests

from encord.api.ml_endpoints import (
    _api_ml_create_model,
    _api_ml_create_training_job,
    _api_ml_delete_model,
    _api_ml_delete_training_iteration,
    _api_ml_get_model,
    _api_ml_get_training_data,
    _api_ml_get_training_status,
    _api_ml_get_weights_download_link,
    _api_ml_list_models,
    _api_ml_update_model,
    _api_project_create_model_attachment,
    _api_project_delete_model_attachment,
    _api_project_list_model_attachments,
    _api_project_predict_classification,
    _api_project_predict_instance_segmentation,
    _api_project_predict_object_detection,
    _api_project_update_model_attachment,
)
from encord.exceptions import EncordException, RequestException
from encord.http.v2.api_client import ApiClient
from encord.objects.ml_models import (
    ModelArchitecture,
    ModelCreateRequest,
    ModelIteration,
    ModelIterationPolicy,
    ModelIterationTrainingData,
    ModelPretrainedWeightsType,
    ModelsListOrderBy,
    ModelTrainingRequest,
    ModelTrainingStatus,
    ModelUpdateRequest,
    ModelWithIterations,
    PredictionClassificationRequest,
    PredictionClassificationResultItem,
    PredictionInstanceSegmentationRequest,
    PredictionInstanceSegmentationResultItem,
    PredictionObjectDetectionRequest,
    PredictionObjectDetectionResultItem,
    ProjectModelAttachRequest,
    ProjectModelUpdateRequest,
    ProjectModelWithIterations,
)

LONG_POLLING_RESPONSE_RETRY_N = 3
LONG_POLLING_SLEEP_ON_FAILURE_SECONDS = 10
LONG_POLLING_MAX_REQUEST_TIME_SECONDS = 60

logger = logging.getLogger(__name__)


class MlModelsClient:
    """
    Client for interacting with Encord's ML models functionality. This client provides methods
    to create, manage, and use machine learning models within Encord, including classification,
    object detection, and instance segmentation models.
    """

    def __init__(self, api_client: ApiClient) -> None:
        """
        Initialize the ML Models client.

        Args:
            api_client: An authenticated ApiClient instance
        """
        self._api_client = api_client

    def create_model(
        self,
        *,
        features: List[str],
        model: ModelArchitecture,
        title: str,
        description: Optional[str],
    ) -> ModelWithIterations:
        """
        Create a new model in Encord.

        Args:
            features: List of feature names that define the model's output layer structure (e.g. ["car", "person"]).
                These features are directly mapped to neurons in the model's final layer and remain fixed across
                all training iterations. The number and names of features cannot be changed without rebuilding
                the model's architecture, since they determine the size and structure of the output layer.
                This fixed structure enables several key capabilities:
                1. Transfer Learning: The model can be retrained on new datasets while preserving its
                   learned feature detectors, since the output layer structure stays consistent
                2. Cross-Project Usage: The same model can be used across different projects by mapping
                   its fixed features to different ontology features in each project
                3. Flexible Inference: A model trained to detect "vehicle" can be mapped to detect
                   "car", "truck" etc. in different projects based on their specific ontologies
            model: The architecture type of the model to create
            title: Title for the model
            description: Optional description for the model

        Returns:
            ModelWithIterations: The created model and its iterations
        """
        return _api_ml_create_model(
            client=self._api_client,
            body=ModelCreateRequest(
                features=features,
                model=model,
                title=title,
                description=description,
            ),
        )

    def get_model(
        self,
        *,
        model_uuid: UUID,
    ) -> ModelWithIterations:
        """
        Get information about a specific model.

        Args:
            model_uuid: UUID of the model to get information for

        Returns:
            ModelWithIterations: Information about the requested model
        """
        return _api_ml_get_model(
            model_uuid,
            client=self._api_client,
        )

    def list_models(
        self,
        *,
        order_by: ModelsListOrderBy,
        order_asc: bool,
        query: Optional[str],
    ) -> Iterable[ModelWithIterations]:
        """
        List available models with filtering.

        Args:
            order_by: Field to order results by
            order_asc: True for ascending order, False for descending
            query: Optional search query to filter results

        Returns:
            Iterable[ModelWithIterations]: Iterator of models matching the specified criteria
        """
        yield from _api_ml_list_models(
            client=self._api_client,
            order_by=order_by,
            order_asc=order_asc,
            query=query,
        )

    def delete_model(
        self,
        *,
        model_uuid: UUID,
    ) -> None:
        """
        Delete a model.

        Args:
            model_uuid: UUID of the model to delete
        """
        return _api_ml_delete_model(
            model_uuid,
            client=self._api_client,
        )

    def update_model(
        self,
        *,
        model_uuid: UUID,
        title: Optional[str],
        description: Optional[str],
    ) -> ModelWithIterations:
        """
        Update a model's metadata.

        Args:
            model_uuid: UUID of the model to update
            title: New title for the model
            description: New description for the model

        Returns:
            ModelWithIterations: Updated model information
        """
        return _api_ml_update_model(
            model_uuid,
            client=self._api_client,
            body=ModelUpdateRequest(
                description=description,
                title=title,
            ),
        )

    def create_training_job(
        self,
        *,
        model_uuid: UUID,
        batch_size: int,
        epochs: int,
        features_mapping: Dict[UUID, Dict[str, List[str]]],
        labels_uuids: List[UUID],
        pretrained_training_uuid: Optional[UUID],
        pretrained_weights_type: Optional[ModelPretrainedWeightsType],
    ) -> UUID:
        """
        Create a new training job for a model.

        Args:
            model_uuid: UUID of the model to train
            batch_size: Training batch size
            epochs: Number of training epochs
            features_mapping: Maps project UUIDs to mappings between ontology features and model features.
                This complex structure allows training examples for model features to be sourced from multiple
                projects with different ontologies. For example:
                ```json
                {
                    project_uuid_0: {
                        "ontology_0_feature_0": ["model_feature_0"],
                        "ontology_0_feature_1": ["model_feature_1"]
                    },
                    project_uuid_1: {
                        "ontology_1_feature_0": ["model_feature_0", "model_feature_1"]
                    }
                }
                ```
                In this case:
                - Training examples for model_feature_0 will come from:
                    - project_uuid_0's ontology_0_feature_0
                    - project_uuid_1's ontology_1_feature_0
                - Training examples for model_feature_1 will come from:
                    - project_uuid_0's ontology_0_feature_1
                    - project_uuid_1's ontology_1_feature_0

                The project-level mapping is essential because:
                1. Different projects can use different ontologies
                2. The same semantic concept (e.g. "car") might have different feature IDs across ontologies
                3. Allows flexibly combining training data from multiple sources while maintaining correct
                   mappings between ontology features and model features
            labels_uuids: List of label UUIDs to use for training
            pretrained_training_uuid: Optional UUID of previous training to use for transfer learning
            pretrained_weights_type: Optional type of pretrained weights to use

        Returns:
            UUID: The unique identifier of the created training job
        """
        return _api_ml_create_training_job(
            model_uuid,
            client=self._api_client,
            body=ModelTrainingRequest(
                batch_size=batch_size,
                epochs=epochs,
                features_mapping=features_mapping,
                labels_uuids=labels_uuids,
                pretrained_training_uuid=pretrained_training_uuid,
                pretrained_weights_type=pretrained_weights_type,
            ),
        )

    def get_training_status(
        self,
        *,
        model_uuid: UUID,
        training_uuid: UUID,
        timeout_seconds: int = 7 * 24 * 60 * 60,  # 7 days
    ) -> ModelIteration:
        """
        Get the status of a training job.

        Args:
            model_uuid: UUID of the model being trained
            training_uuid: UUID of the training job
            timeout_seconds: Maximum time to wait for training completion. Defaults to 7 days.

        Returns:
            ModelIteration: Information about the training iteration

        Raises:
            EncordException: If training encountered an error
            ValueError: If status response is invalid
            RequestException: If there are network connectivity issues
        """
        failed_requests_count = 0
        polling_start_timestamp = time.perf_counter()

        while True:
            try:
                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                logger.info(f"get_training_status started polling call {polling_elapsed_seconds=}")

                tmp_res = _api_ml_get_training_status(
                    model_uuid,
                    training_uuid,
                    client=self._api_client,
                    timeout_seconds=min(
                        polling_available_seconds,
                        LONG_POLLING_MAX_REQUEST_TIME_SECONDS,
                    ),
                )

                if tmp_res.status == ModelTrainingStatus.DONE:
                    logger.info(f"get_training_status completed with training_uuid={training_uuid}.")

                polling_elapsed_seconds = ceil(time.perf_counter() - polling_start_timestamp)
                polling_available_seconds = max(0, timeout_seconds - polling_elapsed_seconds)

                if polling_available_seconds == 0 or tmp_res.status in [
                    ModelTrainingStatus.DONE,
                    ModelTrainingStatus.ERROR,
                ]:
                    res = tmp_res
                    break

                failed_requests_count = 0
            except (requests.exceptions.RequestException, RequestException):
                failed_requests_count += 1

                if failed_requests_count >= LONG_POLLING_RESPONSE_RETRY_N:
                    raise

                time.sleep(LONG_POLLING_SLEEP_ON_FAILURE_SECONDS)

        if res.status == ModelTrainingStatus.DONE:
            if res.result is None:
                raise ValueError(f"{res.status=}, res.result should not be None with DONE status")

            return res.result
        elif res.status == ModelTrainingStatus.ERROR:
            raise EncordException(f"get_training_status error occurred, {model_uuid=}, {training_uuid=}")
        else:
            raise ValueError(f"{res.status=}, only DONE and ERROR status is expected after successful long polling")

    def get_training_data(
        self,
        *,
        model_uuid: UUID,
        training_uuid: UUID,
    ) -> Iterable[ModelIterationTrainingData]:
        """
        Get information about data used in a training iteration.

        Args:
            model_uuid: UUID of the model
            training_uuid: UUID of the training iteration

        Returns:
            Iterable[ModelIterationTrainingData]: Iterator of training data items
        """
        yield from _api_ml_get_training_data(
            model_uuid,
            training_uuid,
            client=self._api_client,
        )

    def get_weights_download_link(
        self,
        *,
        model_uuid: UUID,
        training_uuid: UUID,
    ) -> str:
        """
        Get a download link for trained model weights.

        Args:
            model_uuid: UUID of the model
            training_uuid: UUID of the training iteration

        Returns:
            str: URL for downloading model weights
        """
        return _api_ml_get_weights_download_link(
            model_uuid,
            training_uuid,
            client=self._api_client,
        )

    def delete_training_iteration(
        self,
        *,
        model_uuid: UUID,
        training_uuid: UUID,
    ) -> None:
        """
        Delete a training iteration.

        Args:
            model_uuid: UUID of the model
            training_uuid: UUID of the training iteration to delete
        """
        return _api_ml_delete_training_iteration(
            model_uuid,
            training_uuid,
            client=self._api_client,
        )

    def create_model_attachment(
        self,
        *,
        project_uuid: UUID,
        features_mapping: Dict[str, str],
        iteration_policy: ModelIterationPolicy,
        model_uuid: UUID,
        training_uuids: Optional[List[UUID]],
    ) -> ProjectModelWithIterations:
        """
        Attach a model to a project by mapping the model's features to corresponding ontology features in the project.
        This allows a single trained model to be reused across different projects, even if they use different
        ontologies to represent the same concepts.

        Args:
            project_uuid: UUID of the project to attach the model to
            features_mapping: Maps model features to project ontology features. For example:
                ```json
                {
                    "model_feature_0": "ontology_feature_hash_1",
                    "model_feature_1": "ontology_feature_hash_2"
                }
                ```
                This mapping connects each model feature (e.g. "car" detection) to the corresponding
                feature in the project's ontology. Since different projects may use different
                ontologies with different feature hashes for the same concept, this mapping allows
                the same trained model to be reused across projects by correctly mapping its
                features to each project's specific ontology structure.
            iteration_policy: Policy for model iteration selection
            model_uuid: UUID of the model to attach
            training_uuids: Optional list of specific training iterations to use. Only required
                when iteration_policy is set to MANUAL_SELECTION.

        Returns:
            ProjectModelWithIterations: Information about the created model attachment
        """
        return _api_project_create_model_attachment(
            project_uuid,
            client=self._api_client,
            body=ProjectModelAttachRequest(
                features_mapping=features_mapping,
                iteration_policy=iteration_policy,
                model_uuid=model_uuid,
                training_uuids=training_uuids,
            ),
        )

    def list_model_attachments(
        self,
        *,
        project_uuid: UUID,
    ) -> Iterable[ProjectModelWithIterations]:
        """
        List models attached to a project.

        Args:
            project_uuid: UUID of the project

        Returns:
            Iterable[ProjectModelWithIterations]: Iterator of attached model information
        """
        yield from _api_project_list_model_attachments(
            project_uuid,
            client=self._api_client,
        )

    def update_model_attachment(
        self,
        *,
        project_uuid: UUID,
        project_model_uuid: UUID,
        features_mapping: Dict[str, str],
        iteration_policy: ModelIterationPolicy,
        training_uuids: Optional[List[UUID]],
    ) -> ProjectModelWithIterations:
        """
        Update how a model is attached to a project by modifying its feature mappings and iteration settings.
        This allows you to change how the model's features map to the project's ontology features,
        or update which model iterations are used for inference.

        Args:
            project_uuid: UUID of the project
            project_model_uuid: UUID identifying this specific model attachment to the project
            features_mapping: Maps model features to project ontology features. For example:
                ```json
                {
                    "model_feature_0": "new_ontology_feature_hash_1",
                    "model_feature_1": "new_ontology_feature_hash_2"
                }
                ```
                This lets you remap model features to different ontology features - useful
                when the project's ontology has changed or if you want the model to detect
                different classes than it was originally mapped to.
            iteration_policy: Updated policy for selecting which trained iteration of the model to use.
                Can be changed between automatically using latest iteration or manually specified ones.
            training_uuids: Optional list of specific training iterations to use. Only required
                when iteration_policy is set to MANUAL_SELECTION. Allows cherry-picking which
                trained versions of the model to use for inference.

        Returns:
            ProjectModelWithIterations: Information about the updated model attachment
        """
        return _api_project_update_model_attachment(
            project_uuid,
            project_model_uuid,
            client=self._api_client,
            body=ProjectModelUpdateRequest(
                features_mapping=features_mapping,
                iteration_policy=iteration_policy,
                training_uuids=training_uuids,
            ),
        )

    def delete_model_attachment(
        self,
        *,
        project_uuid: UUID,
        project_model_uuid: UUID,
    ) -> None:
        """
        Remove a model attachment from a project.

        Args:
            project_uuid: UUID of the project
            project_model_uuid: UUID of the model attachment to project
        """
        return _api_project_delete_model_attachment(
            project_uuid,
            project_model_uuid,
            client=self._api_client,
        )

    def predict_classification(
        self,
        *,
        project_uuid: UUID,
        project_model_uuid: UUID,
        training_uuid: UUID,
        data_uuid: Optional[UUID],
        data_path: Optional[Path],
        frame_range_from: Optional[int],
        frame_range_to: Optional[int],
        conf_thresh: float,
    ) -> Dict[int, Optional[PredictionClassificationResultItem]]:
        """
        Run classification prediction on either data_uuid or data_path.

        Args:
            project_uuid: UUID of the project
            project_model_uuid: UUID of the model attachment to project
            training_uuid: UUID of the training iteration to use
            data_uuid: Optional UUID of data to predict on
            data_path: Optional path to local data file
            frame_range_from: Optional starting frame for prediction (first frame if not set)
            frame_range_to: Optional ending frame for prediction (last frame if not set)
            conf_thresh: Confidence threshold for predictions (0.0 - 1.0)

        Returns:
            Dict[int, Optional[PredictionClassificationResultItem]]: Dictionary mapping frame numbers to classification results
        """
        return _api_project_predict_classification(
            project_uuid,
            project_model_uuid,
            training_uuid,
            client=self._api_client,
            body=PredictionClassificationRequest(
                conf_thresh=conf_thresh,
                data_uuid=data_uuid,
                data_base64=base64.b64encode(Path(data_path).read_bytes()).decode("utf-8") if data_path else None,
                frame_range_from=frame_range_from,
                frame_range_to=frame_range_to,
            ),
        ).result

    def predict_instance_segmentation(
        self,
        *,
        project_uuid: UUID,
        project_model_uuid: UUID,
        training_uuid: UUID,
        data_uuid: Optional[UUID],
        data_path: Optional[Path],
        frame_range_from: Optional[int],
        frame_range_to: Optional[int],
        allocation_enabled: bool,
        conf_thresh: float,
        iou_thresh: float,
        rdp_thresh: Optional[float],
    ) -> Dict[int, List[PredictionInstanceSegmentationResultItem]]:
        """
        Run instance segmentation prediction on either data_uuid or data_path.

        Args:
            project_uuid: UUID of the project
            project_model_uuid: UUID of the model attachment to project
            training_uuid: UUID of the training iteration to use
            data_uuid: Optional UUID of data to predict on
            data_path: Optional path to local data file
            frame_range_from: Optional starting frame for prediction (first frame if not set)
            frame_range_to: Optional ending frame for prediction (last frame if not set)
            allocation_enabled: Whether to enable object id tracking
            conf_thresh: Confidence threshold for predictions (0.0 - 1.0)
            iou_thresh: Intersection over Union threshold (0.0 - 1.0)
            rdp_thresh: Optional Ramer-Douglas-Peucker algorithm threshold for polygon simplification

        Returns:
            Dict[int, List[PredictionInstanceSegmentationResultItem]]: Dictionary mapping frame numbers to lists of instance segmentation results
        """
        return _api_project_predict_instance_segmentation(
            project_uuid,
            project_model_uuid,
            training_uuid,
            client=self._api_client,
            body=PredictionInstanceSegmentationRequest(
                allocation_enabled=allocation_enabled,
                conf_thresh=conf_thresh,
                data_uuid=data_uuid,
                data_base64=base64.b64encode(Path(data_path).read_bytes()).decode("utf-8") if data_path else None,
                frame_range_from=frame_range_from,
                frame_range_to=frame_range_to,
                iou_thresh=iou_thresh,
                rdp_thresh=rdp_thresh,
            ),
        ).result

    def predict_object_detection(
        self,
        *,
        project_uuid: UUID,
        project_model_uuid: UUID,
        training_uuid: UUID,
        data_uuid: Optional[UUID],
        data_path: Optional[Path],
        frame_range_from: Optional[int],
        frame_range_to: Optional[int],
        allocation_enabled: bool,
        conf_thresh: float,
        iou_thresh: float,
    ) -> Dict[int, List[PredictionObjectDetectionResultItem]]:
        """
        Run object detection prediction on either data_uuid or data_path.

        Args:
            project_uuid: UUID of the project
            project_model_uuid: UUID of the model attachment to project
            training_uuid: UUID of the training iteration to use
            data_uuid: Optional UUID of data to predict on
            data_path: Optional path to local data file
            frame_range_from: Optional starting frame for prediction (first frame if not set)
            frame_range_to: Optional ending frame for prediction (last frame if not set)
            allocation_enabled: Whether to enable object id tracking
            conf_thresh: Confidence threshold for predictions (0.0 - 1.0)
            iou_thresh: Intersection over Union threshold (0.0 - 1.0)

        Returns:
            Dict[int, List[PredictionObjectDetectionResultItem]]: Dictionary mapping frame numbers to lists of object detection results
        """
        return _api_project_predict_object_detection(
            project_uuid,
            project_model_uuid,
            training_uuid,
            client=self._api_client,
            body=PredictionObjectDetectionRequest(
                allocation_enabled=allocation_enabled,
                conf_thresh=conf_thresh,
                data_uuid=data_uuid,
                data_base64=base64.b64encode(Path(data_path).read_bytes()).decode("utf-8") if data_path else None,
                frame_range_from=frame_range_from,
                frame_range_to=frame_range_to,
                iou_thresh=iou_thresh,
            ),
        ).result
