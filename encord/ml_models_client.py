from typing import Dict, List, Union
from uuid import UUID

from encord import EncordUserClient
from encord.objects.ml_models import (
    ApiIterationPolicy,
    ApiModelArchitecture,
    ApiModelIterationTrainingDataItem,
    ApiPretrainedWeightsType,
    ApiReadModelsOrderBy,
    ApiRequestClassificationPrediction,
    ApiRequestInstanceSegmentationPrediction,
    ApiRequestModelAttachToProject,
    ApiRequestModelInsert,
    ApiRequestModelOperationsTrain,
    ApiRequestModelPatch,
    ApiRequestObjectDetectionPrediction,
    ApiRequestProjectModelUpdate,
    ApiResponseGetTrainingResultDone,
    ApiResponseGetTrainingResultError,
    ApiResponseGetTrainingResultPending,
    ApiResponseModelRead,
    ApiResponseModelReadItem,
    ApiResponseProjectModelReadItem,
)
from encord.utilities.ml_endpoints import (
    _api_ml_create_model,
    _api_ml_create_training_job,
    _api_ml_delete_model,
    _api_ml_delete_training_iteration,
    _api_ml_get_model_info,
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


class MlModelsClient:
    def __init__(self, user_client: EncordUserClient) -> None:
        self.user_client = user_client

    def create_model(
        self,
        features: List[str],
        model: ApiModelArchitecture,
        title: str,
        description: Union[None, str],
    ) -> UUID:
        return _api_ml_create_model(
            client=self.user_client._api_client,
            body=ApiRequestModelInsert(
                features=features,
                model=model,
                title=title,
                description=description,
            ),
        )

    def get_model_info(
        self,
        model_uuid: UUID,
    ) -> ApiResponseModelReadItem:
        return _api_ml_get_model_info(
            model_uuid,
            client=self.user_client._api_client,
        )

    def delete_model(
        self,
        model_uuid: UUID,
    ) -> None:
        return _api_ml_delete_model(
            model_uuid,
            client=self.user_client._api_client,
        )

    def list_models(
        self,
        order_by: ApiReadModelsOrderBy,
        order_asc: bool,
        limit: int,
        offset: int,
        query: Union[None, str],
    ) -> ApiResponseModelRead:
        return _api_ml_list_models(
            client=self.user_client._api_client,
            order_by=order_by,
            order_asc=order_asc,
            limit=limit,
            offset=offset,
            query=query,
        )

    def update_model(
        self,
        model_uuid: UUID,
        description: Union[None, str],
        title: Union[None, str],
    ) -> ApiResponseModelReadItem:
        return _api_ml_update_model(
            model_uuid,
            client=self.user_client._api_client,
            body=ApiRequestModelPatch(
                description=description,
                title=title,
            ),
        )

    def create_training_job(
        self,
        model_uuid: UUID,
        batch_size: int,
        epochs: int,
        features_mapping: Dict[UUID, Dict[str, list[str]]],
        labels_uuids: List[UUID],
        pretrained_training_uuid: Union[None, UUID],
        pretrained_weights_type: Union[ApiPretrainedWeightsType, None],
    ) -> UUID:
        return _api_ml_create_training_job(
            model_uuid,
            client=self.user_client._api_client,
            body=ApiRequestModelOperationsTrain(
                batch_size=batch_size,
                epochs=epochs,
                features_mapping=features_mapping,
                labels_uuids=labels_uuids,
                pretrained_training_uuid=pretrained_training_uuid,
                pretrained_weights_type=pretrained_weights_type,
            ),
        )

    # TODO tests below

    # TODO long polling
    def get_training_status(
        self,
        model_uuid: UUID,
        training_uuid: UUID,
        timeout_seconds: Union[None, int] = 0,
    ) -> Union[
        ApiResponseGetTrainingResultDone,
        ApiResponseGetTrainingResultError,
        ApiResponseGetTrainingResultPending,
    ]:
        return _api_ml_get_training_status(
            model_uuid,
            training_uuid,
            client=self.user_client._api_client,
            timeout_seconds=timeout_seconds,
        )

    def delete_training_iteration(
        self,
        model_uuid: UUID,
        training_uuid: UUID,
    ) -> None:
        return _api_ml_delete_training_iteration(
            model_uuid,
            training_uuid,
            client=self.user_client._api_client,
        )

    def get_training_data(
        self,
        model_uuid: UUID,
        training_uuid: UUID,
    ) -> List[ApiModelIterationTrainingDataItem]:
        return _api_ml_get_training_data(
            model_uuid,
            training_uuid,
            client=self.user_client._api_client,
        )

    def get_weights_download_link(
        self,
        model_uuid: UUID,
        training_uuid: UUID,
    ) -> str:
        return _api_ml_get_weights_download_link(
            model_uuid,
            training_uuid,
            client=self.user_client._api_client,
        )

    def list_model_attachments(
        self,
        project_uuid: UUID,
    ) -> List[ApiResponseProjectModelReadItem]:
        return _api_project_list_model_attachments(
            project_uuid,
            client=self.user_client._api_client,
        )

    def create_model_attachment(
        self,
        project_uuid: UUID,
        features_mapping: Dict,
        iteration_policy: ApiIterationPolicy,
        model_uuid: UUID,
        training_uuids: Union[List[UUID], None],
    ) -> None:
        return _api_project_create_model_attachment(
            project_uuid,
            client=self.user_client._api_client,
            body=ApiRequestModelAttachToProject(
                features_mapping=features_mapping,
                iteration_policy=iteration_policy,
                model_uuid=model_uuid,
                training_uuids=training_uuids,
            ),
        )

    def delete_model_attachment(
        self,
        project_uuid: UUID,
        project_model_uuid: UUID,
    ) -> None:
        return _api_project_delete_model_attachment(
            project_uuid,
            project_model_uuid,
            client=self.user_client._api_client,
        )

    def update_model_attachment(
        self,
        project_uuid: UUID,
        project_model_uuid: UUID,
        features_mapping: Dict,
        iteration_policy: ApiIterationPolicy,
        training_uuids: Union[List[UUID], None],
    ) -> None:
        return _api_project_update_model_attachment(
            project_uuid,
            project_model_uuid,
            client=self.user_client._api_client,
            body=ApiRequestProjectModelUpdate(
                features_mapping=features_mapping,
                iteration_policy=iteration_policy,
                training_uuids=training_uuids,
            ),
        )

    def predict_classification(
        self,
        project_uuid: UUID,
        project_model_uuid: UUID,
        training_uuid: UUID,
        classifications_index: List[Dict],
        conf_thresh: float,
        data_uuid: UUID,
        frame_range_from: int,
        frame_range_to: int,
    ) -> Dict:
        return _api_project_predict_classification(
            project_uuid,
            project_model_uuid,
            training_uuid,
            client=self.user_client._api_client,
            body=ApiRequestClassificationPrediction(
                classifications_index=classifications_index,
                conf_thresh=conf_thresh,
                data_uuid=data_uuid,
                frame_range_from=frame_range_from,
                frame_range_to=frame_range_to,
            ),
        )

    def predict_instance_segmentation(
        self,
        project_uuid: UUID,
        project_model_uuid: UUID,
        training_uuid: UUID,
        allocation_enabled: bool,
        conf_thresh: float,
        data_uuid: UUID,
        frame_range_from: int,
        frame_range_to: int,
        iou_thresh: float,
        rdp_thresh: Union[None, float],
    ) -> Dict:
        return _api_project_predict_instance_segmentation(
            project_uuid,
            project_model_uuid,
            training_uuid,
            client=self.user_client._api_client,
            body=ApiRequestInstanceSegmentationPrediction(
                allocation_enabled=allocation_enabled,
                conf_thresh=conf_thresh,
                data_uuid=data_uuid,
                frame_range_from=frame_range_from,
                frame_range_to=frame_range_to,
                iou_thresh=iou_thresh,
                rdp_thresh=rdp_thresh,
            ),
        )

    def predict_object_detection(
        self,
        project_uuid: UUID,
        project_model_uuid: UUID,
        training_uuid: UUID,
        allocation_enabled: bool,
        conf_thresh: float,
        data_uuid: UUID,
        frame_range_from: int,
        frame_range_to: int,
        iou_thresh: float,
    ) -> Dict:
        return _api_project_predict_object_detection(
            project_uuid,
            project_model_uuid,
            training_uuid,
            client=self.user_client._api_client,
            body=ApiRequestObjectDetectionPrediction(
                allocation_enabled=allocation_enabled,
                conf_thresh=conf_thresh,
                data_uuid=data_uuid,
                frame_range_from=frame_range_from,
                frame_range_to=frame_range_to,
                iou_thresh=iou_thresh,
            ),
        )
