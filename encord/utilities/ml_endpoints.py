from typing import (
    Optional,
)
from uuid import UUID

from requests import Request

from encord.http.v2.api_client import ApiClient
from encord.objects.ml_models import (
    ApiModelIterationTrainingData,
    ApiReadModelsOrderBy,
    ApiRequestClassificationPrediction,
    ApiRequestInstanceSegmentationPrediction,
    ApiRequestModelAttachToProject,
    ApiRequestModelInsert,
    ApiRequestModelOperationsTrain,
    ApiRequestModelPatch,
    ApiRequestObjectDetectionPrediction,
    ApiRequestProjectModelUpdate,
    ApiResponseClassificationPredictionResult,
    ApiResponseGetTrainingResult,
    ApiResponseInstanceSegmentationPredictionResult,
    ApiResponseModelRead,
    ApiResponseModelReadItem,
    ApiResponseObjectDetectionPredictionResult,
    ApiResponseProjectModelRead,
)


def _api_ml_list_models(
    *,
    client: ApiClient,
    order_by: ApiReadModelsOrderBy,
    order_asc: bool,
    limit: int,
    offset: int,
    query: Optional[str],
) -> ApiResponseModelRead:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/ml-models",
            params={
                k: v
                for k, v in {
                    "orderBy": order_by,
                    "orderAsc": order_asc,
                    "limit": limit,
                    "offset": offset,
                    "query": query,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiResponseModelRead,
    )


def _api_ml_create_model(
    *,
    client: ApiClient,
    body: ApiRequestModelInsert,
) -> UUID:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/ml-models",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=UUID,
    )


def _api_ml_get_model_info(
    model_uuid: UUID,
    *,
    client: ApiClient,
) -> ApiResponseModelReadItem:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}",
        ).prepare(),
        result_type=ApiResponseModelReadItem,
    )


def _api_ml_delete_model(
    model_uuid: UUID,
    *,
    client: ApiClient,
) -> None:
    return client._request(
        Request(
            method="delete",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}",
        ).prepare(),
        result_type=None,
    )


def _api_ml_update_model(
    model_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestModelPatch,
) -> ApiResponseModelReadItem:
    return client._request(
        Request(
            method="patch",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseModelReadItem,
    )


def _api_ml_delete_training_iteration(
    model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
) -> None:
    return client._request(
        Request(
            method="delete",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/iterations/{training_uuid}",
        ).prepare(),
        result_type=None,
    )


def _api_ml_get_training_data(
    model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
) -> ApiModelIterationTrainingData:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/iterations/{training_uuid}/training-data",
        ).prepare(),
        result_type=ApiModelIterationTrainingData,
    )


def _api_ml_get_weights_download_link(
    model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
) -> str:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/iterations/{training_uuid}/weights-link",
        ).prepare(),
        result_type=str,
    )


def _api_ml_create_training_job(
    model_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestModelOperationsTrain,
) -> UUID:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/trainings",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=UUID,
    )


def _api_ml_get_training_status(
    model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    timeout_seconds: Optional[int] = 0,
) -> ApiResponseGetTrainingResult:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/{training_uuid}/trainings",
            params={
                k: v
                for k, v in {
                    "timeoutSeconds": timeout_seconds,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiResponseGetTrainingResult,
    )


def _api_project_list_model_attachments(
    project_uuid: UUID,
    *,
    client: ApiClient,
) -> ApiResponseProjectModelRead:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments",
        ).prepare(),
        result_type=ApiResponseProjectModelRead,
    )


def _api_project_create_model_attachment(
    project_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestModelAttachToProject,
) -> None:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def _api_project_delete_model_attachment(
    project_uuid: UUID,
    project_model_uuid: UUID,
    *,
    client: ApiClient,
) -> None:
    return client._request(
        Request(
            method="delete",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}",
        ).prepare(),
        result_type=None,
    )


def _api_project_update_model_attachment(
    project_uuid: UUID,
    project_model_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestProjectModelUpdate,
) -> None:
    return client._request(
        Request(
            method="patch",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def _api_project_predict_classification(
    project_uuid: UUID,
    project_model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestClassificationPrediction,
) -> ApiResponseClassificationPredictionResult:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}/iterations/{training_uuid}/classification/predict",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseClassificationPredictionResult,
    )


def _api_project_predict_instance_segmentation(
    project_uuid: UUID,
    project_model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestInstanceSegmentationPrediction,
) -> ApiResponseInstanceSegmentationPredictionResult:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}/iterations/{training_uuid}/instance-segmentation/predict",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseInstanceSegmentationPredictionResult,
    )


def _api_project_predict_object_detection(
    project_uuid: UUID,
    project_model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestObjectDetectionPrediction,
) -> ApiResponseObjectDetectionPredictionResult:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}/iterations/{training_uuid}/object-detection/predict",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseObjectDetectionPredictionResult,
    )
