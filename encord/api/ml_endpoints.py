from typing import (
    Iterable,
    Optional,
)
from uuid import UUID

from requests import Request

from encord.http.v2.api_client import ApiClient
from encord.objects.ml_models import (
    ModelCreateRequest,
    ModelIterationTrainingData,
    ModelIterationTrainingDataListRequest,
    ModelsListOrderBy,
    ModelsListRequest,
    ModelTrainingRequest,
    ModelTrainingResponse,
    ModelUpdateRequest,
    ModelWithIterations,
    PredictionClassificationRequest,
    PredictionClassificationResponse,
    PredictionInstanceSegmentationRequest,
    PredictionInstanceSegmentationResponse,
    PredictionObjectDetectionRequest,
    PredictionObjectDetectionResponse,
    ProjectModelAttachRequest,
    ProjectModelsListRequest,
    ProjectModelUpdateRequest,
    ProjectModelWithIterations,
)


def _api_ml_create_model(
    *,
    client: ApiClient,
    body: ModelCreateRequest,
) -> ModelWithIterations:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/ml-models",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=ModelWithIterations,
    )


def _api_ml_get_model(
    model_uuid: UUID,
    *,
    client: ApiClient,
) -> ModelWithIterations:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}",
        ).prepare(),
        result_type=ModelWithIterations,
    )


def _api_ml_list_models(
    *,
    client: ApiClient,
    order_by: ModelsListOrderBy,
    order_asc: bool,
    query: Optional[str],
) -> Iterable[ModelWithIterations]:
    yield from client.get_paged_iterator(
        "ml-models",
        params=ModelsListRequest(
            order_by=order_by,
            order_asc=order_asc,
            query=query,
            page_token=None,
        ),
        result_type=ModelWithIterations,
    )


def _api_ml_delete_model(
    model_uuid: UUID,
    *,
    client: ApiClient,
) -> None:
    client._request(
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
    body: ModelUpdateRequest,
) -> ModelWithIterations:
    return client._request(
        Request(
            method="patch",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=ModelWithIterations,
    )


def _api_ml_create_training_job(
    model_uuid: UUID,
    *,
    client: ApiClient,
    body: ModelTrainingRequest,
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
) -> ModelTrainingResponse:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/iterations/{training_uuid}/training",
            params={
                k: v
                for k, v in {
                    "timeoutSeconds": timeout_seconds,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ModelTrainingResponse,
    )


def _api_ml_get_training_data(
    model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
) -> Iterable[ModelIterationTrainingData]:
    yield from client.get_paged_iterator(
        f"ml-models/{model_uuid}/iterations/{training_uuid}/training-data",
        params=ModelIterationTrainingDataListRequest(
            page_token=None,
        ),
        result_type=ModelIterationTrainingData,
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


def _api_ml_delete_training_iteration(
    model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
) -> None:
    client._request(
        Request(
            method="delete",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/iterations/{training_uuid}",
        ).prepare(),
        result_type=None,
    )


def _api_project_create_model_attachment(
    project_uuid: UUID,
    *,
    client: ApiClient,
    body: ProjectModelAttachRequest,
) -> ProjectModelWithIterations:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=ProjectModelWithIterations,
    )


def _api_project_list_model_attachments(
    project_uuid: UUID,
    *,
    client: ApiClient,
) -> Iterable[ProjectModelWithIterations]:
    yield from client.get_paged_iterator(
        f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments",
        params=ProjectModelsListRequest(
            page_token=None,
        ),
        result_type=ProjectModelWithIterations,
    )


def _api_project_update_model_attachment(
    project_uuid: UUID,
    project_model_uuid: UUID,
    *,
    client: ApiClient,
    body: ProjectModelUpdateRequest,
) -> ProjectModelWithIterations:
    return client._request(
        Request(
            method="patch",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=ProjectModelWithIterations,
    )


def _api_project_delete_model_attachment(
    project_uuid: UUID,
    project_model_uuid: UUID,
    *,
    client: ApiClient,
) -> None:
    client._request(
        Request(
            method="delete",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}",
        ).prepare(),
        result_type=None,
    )


def _api_project_predict_classification(
    project_uuid: UUID,
    project_model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    body: PredictionClassificationRequest,
) -> PredictionClassificationResponse:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}/iterations/{training_uuid}/classification/predict",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=PredictionClassificationResponse,
    )


def _api_project_predict_instance_segmentation(
    project_uuid: UUID,
    project_model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    body: PredictionInstanceSegmentationRequest,
) -> PredictionInstanceSegmentationResponse:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}/iterations/{training_uuid}/instance-segmentation/predict",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=PredictionInstanceSegmentationResponse,
    )


def _api_project_predict_object_detection(
    project_uuid: UUID,
    project_model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    body: PredictionObjectDetectionRequest,
) -> PredictionObjectDetectionResponse:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}/iterations/{training_uuid}/object-detection/predict",
            json=client._serialise_payload(body),
        ).prepare(),
        result_type=PredictionObjectDetectionResponse,
    )
