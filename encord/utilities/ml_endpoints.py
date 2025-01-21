from typing import (
    Dict,
    List,
    Union,
)
from uuid import UUID

from requests import Request

from encord.http.v2.api_client import ApiClient
from encord.objects.ml_models import (
    ApiModelIterationTrainingDataItem,
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


def _api_ml_list_models(
    *,
    client: ApiClient,
    order_by: ApiReadModelsOrderBy,
    order_asc: bool,
    limit: int,
    offset: int,
    query: Union[None, str],
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
            json=client.serialise_payload(body),
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
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}".format(
                model_uuid=model_uuid,
            ),
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
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}".format(
                model_uuid=model_uuid,
            ),
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
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}".format(
                model_uuid=model_uuid,
            ),
            json=client.serialise_payload(body),
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
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/iterations/{training_uuid}".format(
                model_uuid=model_uuid,
                training_uuid=training_uuid,
            ),
        ).prepare(),
        result_type=None,
    )


def _api_ml_get_training_data(
    model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
) -> List[ApiModelIterationTrainingDataItem]:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/iterations/{training_uuid}/training-data".format(
                model_uuid=model_uuid,
                training_uuid=training_uuid,
            ),
        ).prepare(),
        result_type=List[ApiModelIterationTrainingDataItem],
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
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/iterations/{training_uuid}/weights-link".format(
                model_uuid=model_uuid,
                training_uuid=training_uuid,
            ),
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
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/training".format(
                model_uuid=model_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=UUID,
    )


def _api_ml_get_training_status(
    model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    timeout_seconds: Union[None, int] = 0,
) -> Union[
    ApiResponseGetTrainingResultDone,
    ApiResponseGetTrainingResultError,
    ApiResponseGetTrainingResultPending,
]:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/ml-models/{model_uuid}/{training_uuid}/training".format(
                model_uuid=model_uuid,
                training_uuid=training_uuid,
            ),
            params={
                k: v
                for k, v in {
                    "timeoutSeconds": timeout_seconds,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=Union[
            ApiResponseGetTrainingResultDone,
            ApiResponseGetTrainingResultError,
            ApiResponseGetTrainingResultPending,
        ],
    )


def _api_project_list_model_attachments(
    project_uuid: UUID,
    *,
    client: ApiClient,
) -> List[ApiResponseProjectModelReadItem]:
    return client._request(
        Request(
            method="get",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments".format(
                project_uuid=project_uuid,
            ),
        ).prepare(),
        result_type=List[ApiResponseProjectModelReadItem],
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
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments".format(
                project_uuid=project_uuid,
            ),
            json=client.serialise_payload(body),
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
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}".format(
                project_uuid=project_uuid,
                project_model_uuid=project_model_uuid,
            ),
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
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}".format(
                project_uuid=project_uuid,
                project_model_uuid=project_model_uuid,
            ),
            json=client.serialise_payload(body),
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
) -> Dict:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}/iterations/{training_uuid}/classification/predict".format(
                project_uuid=project_uuid,
                project_model_uuid=project_model_uuid,
                training_uuid=training_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=Dict,
    )


def _api_project_predict_instance_segmentation(
    project_uuid: UUID,
    project_model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestInstanceSegmentationPrediction,
) -> Dict:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}/iterations/{training_uuid}/instance-segmentation/predict".format(
                project_uuid=project_uuid,
                project_model_uuid=project_model_uuid,
                training_uuid=training_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=Dict,
    )


def _api_project_predict_object_detection(
    project_uuid: UUID,
    project_model_uuid: UUID,
    training_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestObjectDetectionPrediction,
) -> Dict:
    return client._request(
        Request(
            method="post",
            url=f"{client._domain}/v2/public/projects/{project_uuid}/models-attachments/{project_model_uuid}/iterations/{training_uuid}/object-detection/predict".format(
                project_uuid=project_uuid,
                project_model_uuid=project_model_uuid,
                training_uuid=training_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=Dict,
    )
