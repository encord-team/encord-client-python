import datetime
from typing import (
    Any,
    Dict,
    List,
    Union,
)
from uuid import UUID

from requests import Request

from encord.api_v2.models import (
    ApiAnnotationTaskState,
    ApiClientMetadataSchema,
    ApiClientMetadataSchemaOrmRead,
    ApiCordDataType,
    ApiFoldersSortBy,
    ApiJobStatusInfo,
    ApiJournalActionTarget,
    ApiJournalActionType,
    ApiJournalRecord,
    ApiLabelReviewTaskStatus,
    ApiLabelValidationState,
    ApiOrganisationUserInfo,
    ApiPaginatedResponseDataset,
    ApiPaginatedResponseDatasetGroup,
    ApiPaginatedResponseFolderGroup,
    ApiPaginatedResponseGroup,
    ApiPaginatedResponseIndexCollection,
    ApiPaginatedResponseIndexFilterPreset,
    ApiPaginatedResponseJournalRecord,
    ApiPaginatedResponseLabelReview,
    ApiPaginatedResponseOntologyGroup,
    ApiPaginatedResponseProjectGroup,
    ApiPaginatedResponseProjectPerformanceCollaboratorData,
    ApiPaginatedResponseProjectUser,
    ApiPaginatedResponseStorageFolder,
    ApiPaginatedResponseStorageItem,
    ApiPaginatedResponseStorageItemUnion,
    ApiPaginatedResponseTask,
    ApiPaginatedResponseUploadUrl,
    ApiProject,
    ApiRequestAddDatasetGroups,
    ApiRequestAddFolderGroups,
    ApiRequestAddOntologyGroups,
    ApiRequestAddProjectGroup,
    ApiRequestCreateDataset,
    ApiRequestCreateFolder,
    ApiRequestDeleteFolderChildren,
    ApiRequestGetItemsBulk,
    ApiRequestIndexCollectionBulkItem,
    ApiRequestIndexCollectionInsert,
    ApiRequestIndexCollectionPreset,
    ApiRequestIndexCollectionUpdate,
    ApiRequestIndexFilterPresetCreate,
    ApiRequestIndexFilterPresetUpdate,
    ApiRequestMoveFolders,
    ApiRequestMoveItems,
    ApiRequestPatchFolder,
    ApiRequestPatchFolderBulk,
    ApiRequestPatchItem,
    ApiRequestPatchItemsBulk,
    ApiRequestPriorities,
    ApiRequestStartTraining,
    ApiRequestStorageItemsMigrate,
    ApiRequestStorageItemsRencode,
    ApiRequestUploadJob,
    ApiRequestUploadSignedUrls,
    ApiResponseBearerToken,
    ApiResponseCancelFolderUploadJob,
    ApiResponseCreateDataset,
    ApiResponseDatasetsWithUserRoles,
    ApiResponseDeletion,
    ApiResponseFolderUploadStatus,
    ApiResponseGetCurrentUser,
    ApiResponseGetTrainingResultDone,
    ApiResponseGetTrainingResultError,
    ApiResponseGetTrainingResultPending,
    ApiResponseIndexCollectionBulkItem,
    ApiResponseLegacyPublic,
    ApiResponseStorageFolder,
    ApiResponseStorageFolderSummary,
    ApiResponseStorageItem,
    ApiResponseStorageItemSummary,
    ApiReviewTaskState,
    ApiStorageFolderConfig,
    ApiStorageItemType,
    ApiTimersGroupBy,
    IndexGetPresetFilterResponsePublicIndexGetPresetFilterIndexPresetsUuidGet,
    LegacyPublicRouteData,
    LegacyPublicUserRouteData,
    OrgCreateMetadataSchemaLegacyMetadataSchema,
    WorkflowExecuteStageActionsBodyItem,
)
from encord.http.v2.api_client import ApiClient


def api_legacy_public_route(
    *,
    client: ApiClient,
    body: LegacyPublicRouteData,
    authorization: str,
    resource_id: UUID,
    resource_type: Union[None, str],
    x_cloud_trace_context: Union[None, str],
) -> ApiResponseLegacyPublic:
    return client.request(
        Request(
            method="post",
            url="/public",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseLegacyPublic,
    )


def api_legacy_public_user_route(
    *,
    client: ApiClient,
    body: LegacyPublicUserRouteData,
    authorization: str,
    x_cloud_trace_context: Union[None, str],
) -> ApiResponseLegacyPublic:
    return client.request(
        Request(
            method="post",
            url="/public/user",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseLegacyPublic,
    )


def api_analytics_get_collaborator_time_metrics(
    *,
    client: ApiClient,
    project_hash: UUID,
    after: datetime.datetime,
    before: Union[None, datetime.datetime],
    group_by: Union[None, ApiTimersGroupBy] = ApiTimersGroupBy.DATAUNIT,
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseProjectPerformanceCollaboratorData:
    return client.request(
        Request(
            method="get",
            url="/v2/public/analytics/collaborators/timers",
            params={
                k: v
                for k, v in {
                    "projectHash": project_hash,
                    "after": after,
                    "before": before,
                    "groupBy": group_by,
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseProjectPerformanceCollaboratorData,
    )


def api_dataset_create_new(
    *,
    client: ApiClient,
    body: ApiRequestCreateDataset,
) -> ApiResponseCreateDataset:
    return client.request(
        Request(
            method="post",
            url="/v2/public/datasets",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseCreateDataset,
    )


def api_dataset_list_all(
    *,
    client: ApiClient,
    title_eq: Union[None, str],
    title_like: Union[None, str],
    description_eq: Union[None, str],
    description_like: Union[None, str],
    created_before: Union[None, datetime.datetime],
    created_after: Union[None, datetime.datetime],
    edited_before: Union[None, datetime.datetime],
    edited_after: Union[None, datetime.datetime],
) -> ApiResponseDatasetsWithUserRoles:
    return client.request(
        Request(
            method="get",
            url="/v2/public/datasets/list",
            params={
                k: v
                for k, v in {
                    "titleEq": title_eq,
                    "titleLike": title_like,
                    "descriptionEq": description_eq,
                    "descriptionLike": description_like,
                    "createdBefore": created_before,
                    "createdAfter": created_after,
                    "editedBefore": edited_before,
                    "editedAfter": edited_after,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiResponseDatasetsWithUserRoles,
    )


def api_dataset_delete_by_id(
    dataset_hash: UUID,
    *,
    client: ApiClient,
) -> None:
    return client.request(
        Request(
            method="delete",
            url="/v2/public/datasets/{dataset_hash}".format(
                dataset_hash=dataset_hash,
            ),
        ).prepare(),
        result_type=None,
    )


def api_dataset_list_groups(
    dataset_hash: UUID,
    *,
    client: ApiClient,
) -> ApiPaginatedResponseDatasetGroup:
    return client.request(
        Request(
            method="get",
            url="/v2/public/datasets/{dataset_hash}/groups".format(
                dataset_hash=dataset_hash,
            ),
        ).prepare(),
        result_type=ApiPaginatedResponseDatasetGroup,
    )


def api_dataset_add_groups(
    dataset_hash: UUID,
    *,
    client: ApiClient,
    body: ApiRequestAddDatasetGroups,
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/datasets/{dataset_hash}/groups".format(
                dataset_hash=dataset_hash,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_dataset_remove_groups(
    dataset_hash: UUID,
    *,
    client: ApiClient,
    group_hash_list: List[UUID],
) -> None:
    return client.request(
        Request(
            method="delete",
            url="/v2/public/datasets/{dataset_hash}/groups".format(
                dataset_hash=dataset_hash,
            ),
            params={
                k: v
                for k, v in {
                    "groupHashList": group_hash_list,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=None,
    )


def api_index_list_collections(
    *,
    client: ApiClient,
    top_level_folder_uuid: Union[None, UUID],
    uuids: Union[List[UUID], None],
    search: Union[None, str],
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseIndexCollection:
    return client.request(
        Request(
            method="get",
            url="/v2/public/index/collections",
            params={
                k: v
                for k, v in {
                    "topLevelFolderUuid": top_level_folder_uuid,
                    "uuids": uuids,
                    "search": search,
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseIndexCollection,
    )


def api_index_create_collection(
    *,
    client: ApiClient,
    body: ApiRequestIndexCollectionInsert,
    top_level_folder_uuid: UUID,
) -> UUID:
    return client.request(
        Request(
            method="post",
            url="/v2/public/index/collections",
            params={
                k: v
                for k, v in {
                    "topLevelFolderUuid": top_level_folder_uuid,
                }.items()
                if v is not None
            },
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=UUID,
    )


def api_index_list_accessible_items(
    collection_id: UUID,
    *,
    client: ApiClient,
    sign_urls: Union[None, bool] = False,
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseStorageItem:
    return client.request(
        Request(
            method="get",
            url="/v2/public/index/collections/{collection_id}/accessible-items".format(
                collection_id=collection_id,
            ),
            params={
                k: v
                for k, v in {
                    "signUrls": sign_urls,
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseStorageItem,
    )


def api_index_add_items_to_collection(
    collection_id: UUID,
    *,
    client: ApiClient,
    body: ApiRequestIndexCollectionBulkItem,
) -> ApiResponseIndexCollectionBulkItem:
    return client.request(
        Request(
            method="post",
            url="/v2/public/index/collections/{collection_id}/add-items".format(
                collection_id=collection_id,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseIndexCollectionBulkItem,
    )


def api_index_add_preset_items_to_collection(
    collection_id: UUID,
    *,
    client: ApiClient,
    body: ApiRequestIndexCollectionPreset,
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/index/collections/{collection_id}/add-preset-items".format(
                collection_id=collection_id,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_index_list_all_items(
    collection_id: UUID,
    *,
    client: ApiClient,
    sign_urls: Union[None, bool] = False,
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseStorageItemUnion:
    return client.request(
        Request(
            method="get",
            url="/v2/public/index/collections/{collection_id}/all-items".format(
                collection_id=collection_id,
            ),
            params={
                k: v
                for k, v in {
                    "signUrls": sign_urls,
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseStorageItemUnion,
    )


def api_index_remove_items_from_collection(
    collection_id: UUID,
    *,
    client: ApiClient,
    body: ApiRequestIndexCollectionBulkItem,
) -> ApiResponseIndexCollectionBulkItem:
    return client.request(
        Request(
            method="post",
            url="/v2/public/index/collections/{collection_id}/remove-items".format(
                collection_id=collection_id,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseIndexCollectionBulkItem,
    )


def api_index_remove_preset_items_from_collection(
    collection_id: UUID,
    *,
    client: ApiClient,
    body: ApiRequestIndexCollectionPreset,
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/index/collections/{collection_id}/remove-preset-items".format(
                collection_id=collection_id,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_index_delete_collection(
    uuid: UUID,
    *,
    client: ApiClient,
) -> None:
    return client.request(
        Request(
            method="delete",
            url="/v2/public/index/collections/{uuid}".format(
                uuid=uuid,
            ),
        ).prepare(),
        result_type=None,
    )


def api_index_update_collection(
    uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestIndexCollectionUpdate,
) -> None:
    return client.request(
        Request(
            method="patch",
            url="/v2/public/index/collections/{uuid}".format(
                uuid=uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_index_list_presets(
    *,
    client: ApiClient,
    top_level_folder_uuid: Union[None, UUID],
    uuids: Union[List[UUID], None],
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseIndexFilterPreset:
    return client.request(
        Request(
            method="get",
            url="/v2/public/index/presets",
            params={
                k: v
                for k, v in {
                    "topLevelFolderUuid": top_level_folder_uuid,
                    "uuids": uuids,
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseIndexFilterPreset,
    )


def api_index_create_preset(
    *,
    client: ApiClient,
    body: ApiRequestIndexFilterPresetCreate,
    top_level_folder_uuid: UUID,
) -> UUID:
    return client.request(
        Request(
            method="post",
            url="/v2/public/index/presets",
            params={
                k: v
                for k, v in {
                    "topLevelFolderUuid": top_level_folder_uuid,
                }.items()
                if v is not None
            },
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=UUID,
    )


def api_index_get_preset_filter(
    uuid: UUID,
    *,
    client: ApiClient,
) -> IndexGetPresetFilterResponsePublicIndexGetPresetFilterIndexPresetsUuidGet:
    return client.request(
        Request(
            method="get",
            url="/v2/public/index/presets/{uuid}".format(
                uuid=uuid,
            ),
        ).prepare(),
        result_type=IndexGetPresetFilterResponsePublicIndexGetPresetFilterIndexPresetsUuidGet,
    )


def api_index_delete_preset(
    uuid: UUID,
    *,
    client: ApiClient,
) -> None:
    return client.request(
        Request(
            method="delete",
            url="/v2/public/index/presets/{uuid}".format(
                uuid=uuid,
            ),
        ).prepare(),
        result_type=None,
    )


def api_index_update_preset(
    uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestIndexFilterPresetUpdate,
) -> None:
    return client.request(
        Request(
            method="patch",
            url="/v2/public/index/presets/{uuid}".format(
                uuid=uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_ml_model_start_training(
    model_hash: UUID,
    *,
    client: ApiClient,
    body: ApiRequestStartTraining,
) -> UUID:
    return client.request(
        Request(
            method="post",
            url="/v2/public/ml-models/{model_hash}/training".format(
                model_hash=model_hash,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=UUID,
    )


def api_ml_model_get_training_result(
    model_hash: UUID,
    training_hash: UUID,
    *,
    client: ApiClient,
    timeout_seconds: Union[None, int] = 0,
) -> Union[
    ApiResponseGetTrainingResultDone,
    ApiResponseGetTrainingResultError,
    ApiResponseGetTrainingResultPending,
]:
    return client.request(
        Request(
            method="get",
            url="/v2/public/ml-models/{model_hash}/{training_hash}/training".format(
                model_hash=model_hash,
                training_hash=training_hash,
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


def api_ontology_list_groups(
    ontology_hash: UUID,
    *,
    client: ApiClient,
) -> ApiPaginatedResponseOntologyGroup:
    return client.request(
        Request(
            method="get",
            url="/v2/public/ontologies/{ontology_hash}/groups".format(
                ontology_hash=ontology_hash,
            ),
        ).prepare(),
        result_type=ApiPaginatedResponseOntologyGroup,
    )


def api_ontology_add_groups(
    ontology_hash: UUID,
    *,
    client: ApiClient,
    body: ApiRequestAddOntologyGroups,
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/ontologies/{ontology_hash}/groups".format(
                ontology_hash=ontology_hash,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_ontology_remove_groups(
    ontology_hash: UUID,
    *,
    client: ApiClient,
    group_hash_list: List[UUID],
) -> None:
    return client.request(
        Request(
            method="delete",
            url="/v2/public/ontologies/{ontology_hash}/groups".format(
                ontology_hash=ontology_hash,
            ),
            params={
                k: v
                for k, v in {
                    "groupHashList": group_hash_list,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=None,
    )


def api_org_get_metadata_schema_legacy(
    *,
    client: ApiClient,
) -> Union[
    ApiClientMetadataSchemaOrmRead,
    None,
]:
    return client.request(
        Request(
            method="get",
            url="/v2/public/organisation/client-metadata-schema",
        ).prepare(),
        result_type=Union[
            ApiClientMetadataSchemaOrmRead,
            None,
        ],
    )


def api_org_create_metadata_schema_legacy(
    *,
    client: ApiClient,
    body: OrgCreateMetadataSchemaLegacyMetadataSchema,
) -> UUID:
    return client.request(
        Request(
            method="post",
            url="/v2/public/organisation/client-metadata-schema",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=UUID,
    )


def api_org_get_metadata_schema(
    *,
    client: ApiClient,
) -> Union[
    ApiClientMetadataSchema,
    None,
]:
    return client.request(
        Request(
            method="get",
            url="/v2/public/organisation/client-metadata-schema-v2",
        ).prepare(),
        result_type=Union[
            ApiClientMetadataSchema,
            None,
        ],
    )


def api_org_create_metadata_schema(
    *,
    client: ApiClient,
    body: ApiClientMetadataSchema,
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/organisation/client-metadata-schema-v2",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_org_list_journal_records(
    *,
    client: ApiClient,
    include_action_data: Union[None, bool] = False,
    created_after: Union[None, datetime.datetime],
    include_targets: Union[None, List[ApiJournalActionTarget]],
    include_types: Union[None, List[ApiJournalActionType]],
    page_size: Union[None, int] = 1000,
    page_token: Union[None, str],
) -> ApiPaginatedResponseJournalRecord:
    return client.request(
        Request(
            method="get",
            url="/v2/public/organisation/journal-records",
            params={
                k: v
                for k, v in {
                    "includeActionData": include_action_data,
                    "createdAfter": created_after,
                    "includeTargets": include_targets,
                    "includeTypes": include_types,
                    "pageSize": page_size,
                    "pageToken": page_token,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseJournalRecord,
    )


def api_org_get_bulk_journal_records(
    *,
    client: ApiClient,
    body: List[UUID],
) -> ApiPaginatedResponseJournalRecord:
    return client.request(
        Request(
            method="post",
            url="/v2/public/organisation/journal-records/get-bulk",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiPaginatedResponseJournalRecord,
    )


def api_org_get_journal_record(
    record_uuid: UUID,
    *,
    client: ApiClient,
) -> ApiJournalRecord:
    return client.request(
        Request(
            method="get",
            url="/v2/public/organisation/journal-records/{record_uuid}".format(
                record_uuid=record_uuid,
            ),
        ).prepare(),
        result_type=ApiJournalRecord,
    )


def api_project_get_details(
    project_hash: UUID,
    *,
    client: ApiClient,
) -> ApiProject:
    return client.request(
        Request(
            method="get",
            url="/v2/public/projects/{project_hash}".format(
                project_hash=project_hash,
            ),
        ).prepare(),
        result_type=ApiProject,
    )


def api_project_list_datasets(
    project_hash: UUID,
    *,
    client: ApiClient,
) -> ApiPaginatedResponseDataset:
    return client.request(
        Request(
            method="get",
            url="/v2/public/projects/{project_hash}/datasets".format(
                project_hash=project_hash,
            ),
        ).prepare(),
        result_type=ApiPaginatedResponseDataset,
    )


def api_project_list_groups(
    project_hash: UUID,
    *,
    client: ApiClient,
) -> ApiPaginatedResponseProjectGroup:
    return client.request(
        Request(
            method="get",
            url="/v2/public/projects/{project_hash}/groups".format(
                project_hash=project_hash,
            ),
        ).prepare(),
        result_type=ApiPaginatedResponseProjectGroup,
    )


def api_project_add_groups(
    project_hash: UUID,
    *,
    client: ApiClient,
    body: ApiRequestAddProjectGroup,
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/projects/{project_hash}/groups".format(
                project_hash=project_hash,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_project_remove_groups(
    project_hash: UUID,
    *,
    client: ApiClient,
    group_hash_list: List[UUID],
) -> None:
    return client.request(
        Request(
            method="delete",
            url="/v2/public/projects/{project_hash}/groups".format(
                project_hash=project_hash,
            ),
            params={
                k: v
                for k, v in {
                    "groupHashList": group_hash_list,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=None,
    )


def api_project_list_label_branches(
    project_hash: UUID,
    *,
    client: ApiClient,
    branch_name_search: Union[None, str],
) -> List[str]:
    return client.request(
        Request(
            method="get",
            url="/v2/public/projects/{project_hash}/label-branches".format(
                project_hash=project_hash,
            ),
            params={
                k: v
                for k, v in {
                    "branchNameSearch": branch_name_search,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=List[str],
    )


def api_project_get_label_validation_state(
    project_hash: UUID,
    label_hash: UUID,
    *,
    client: ApiClient,
    branch_name: Union[None, str] = "main",
) -> ApiLabelValidationState:
    return client.request(
        Request(
            method="get",
            url="/v2/public/projects/{project_hash}/labels/{label_hash}/validation-state".format(
                project_hash=project_hash,
                label_hash=label_hash,
            ),
            params={
                k: v
                for k, v in {
                    "branchName": branch_name,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiLabelValidationState,
    )


def api_project_set_task_priorities(
    project_hash: UUID,
    *,
    client: ApiClient,
    body: ApiRequestPriorities,
) -> List[
    Union[
        ApiAnnotationTaskState,
        ApiReviewTaskState,
    ],
]:
    return client.request(
        Request(
            method="post",
            url="/v2/public/projects/{project_hash}/priorities".format(
                project_hash=project_hash,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=List[
            Union[
                ApiAnnotationTaskState,
                ApiReviewTaskState,
            ],
        ],
    )


def api_project_list_users(
    project_hash: UUID,
    *,
    client: ApiClient,
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseProjectUser:
    return client.request(
        Request(
            method="get",
            url="/v2/public/projects/{project_hash}/users".format(
                project_hash=project_hash,
            ),
            params={
                k: v
                for k, v in {
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseProjectUser,
    )


def api_workflow_execute_stage_actions(
    project_hash: UUID,
    workflow_stage_uuid: UUID,
    *,
    client: ApiClient,
    body: List["WorkflowExecuteStageActionsBodyItem"],
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/projects/{project_hash}/workflow/stages/{workflow_stage_uuid}/actions".format(
                project_hash=project_hash,
                workflow_stage_uuid=workflow_stage_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_workflow_list_stage_tasks(
    project_hash: UUID,
    workflow_stage_uuid: UUID,
    *,
    client: ApiClient,
    data_title_contains: Union[None, str],
    user_emails: Union[None, List[str]],
    data_hashes: Union[None, List[UUID]],
    dataset_hashes: Union[None, List[UUID]],
    data_types: Union[None, List[ApiCordDataType]],
    statuses: Union[None, List[str]],
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseTask:
    return client.request(
        Request(
            method="get",
            url="/v2/public/projects/{project_hash}/workflow/stages/{workflow_stage_uuid}/tasks".format(
                project_hash=project_hash,
                workflow_stage_uuid=workflow_stage_uuid,
            ),
            params={
                k: v
                for k, v in {
                    "dataTitleContains": data_title_contains,
                    "userEmails": user_emails,
                    "dataHashes": data_hashes,
                    "datasetHashes": dataset_hashes,
                    "dataTypes": data_types,
                    "statuses": statuses,
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseTask,
    )


def api_workflow_list_task_reviews(
    project_hash: UUID,
    workflow_stage_uuid: UUID,
    task_uuid: UUID,
    *,
    client: ApiClient,
    statuses: Union[List[ApiLabelReviewTaskStatus], None],
) -> ApiPaginatedResponseLabelReview:
    return client.request(
        Request(
            method="get",
            url="/v2/public/projects/{project_hash}/workflow/stages/{workflow_stage_uuid}/tasks/{task_uuid}/reviews".format(
                project_hash=project_hash,
                workflow_stage_uuid=workflow_stage_uuid,
                task_uuid=task_uuid,
            ),
            params={
                k: v
                for k, v in {
                    "statuses": statuses,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseLabelReview,
    )


def api_storage_list_root_folders(
    *,
    client: ApiClient,
    search: Union[None, str],
    dataset_synced: Union[None, bool],
    include_org_access: Union[None, bool],
    include_hidden: Union[None, bool] = True,
    order: Union[None, ApiFoldersSortBy] = ApiFoldersSortBy.NAME,
    desc: Union[None, bool] = False,
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseStorageFolder:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders",
            params={
                k: v
                for k, v in {
                    "search": search,
                    "datasetSynced": dataset_synced,
                    "includeOrgAccess": include_org_access,
                    "includeHidden": include_hidden,
                    "order": order,
                    "desc": desc,
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseStorageFolder,
    )


def api_storage_create_folder(
    *,
    client: ApiClient,
    body: ApiRequestCreateFolder,
) -> ApiResponseStorageFolder:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/folders",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseStorageFolder,
    )


def api_storage_move_folders(
    *,
    client: ApiClient,
    body: ApiRequestMoveFolders,
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/folders/move",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_storage_update_folders_bulk(
    *,
    client: ApiClient,
    body: ApiRequestPatchFolderBulk,
) -> ApiPaginatedResponseStorageFolder:
    return client.request(
        Request(
            method="patch",
            url="/v2/public/storage/folders/patch-bulk",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiPaginatedResponseStorageFolder,
    )


def api_storage_get_folder_info(
    folder_uuid: UUID,
    *,
    client: ApiClient,
) -> ApiResponseStorageFolder:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders/{folder_uuid}".format(
                folder_uuid=folder_uuid,
            ),
        ).prepare(),
        result_type=ApiResponseStorageFolder,
    )


def api_storage_delete_folder(
    folder_uuid: UUID,
    *,
    client: ApiClient,
) -> None:
    return client.request(
        Request(
            method="delete",
            url="/v2/public/storage/folders/{folder_uuid}".format(
                folder_uuid=folder_uuid,
            ),
        ).prepare(),
        result_type=None,
    )


def api_storage_update_folder(
    folder_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestPatchFolder,
) -> ApiResponseStorageFolder:
    return client.request(
        Request(
            method="patch",
            url="/v2/public/storage/folders/{folder_uuid}".format(
                folder_uuid=folder_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseStorageFolder,
    )


def api_storage_create_upload_job(
    folder_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestUploadJob,
) -> UUID:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/folders/{folder_uuid}/data-upload-jobs".format(
                folder_uuid=folder_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=UUID,
    )


def api_storage_get_upload_status(
    folder_uuid: UUID,
    upload_job_hash: UUID,
    *,
    client: ApiClient,
    timeout_seconds: int,
) -> ApiResponseFolderUploadStatus:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders/{folder_uuid}/data-upload-jobs/{upload_job_hash}".format(
                folder_uuid=folder_uuid,
                upload_job_hash=upload_job_hash,
            ),
            params={
                k: v
                for k, v in {
                    "timeoutSeconds": timeout_seconds,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiResponseFolderUploadStatus,
    )


def api_storage_cancel_upload_job(
    folder_uuid: UUID,
    upload_job_hash: UUID,
    *,
    client: ApiClient,
) -> ApiResponseCancelFolderUploadJob:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/folders/{folder_uuid}/data-upload-jobs/{upload_job_hash}/cancel".format(
                folder_uuid=folder_uuid,
                upload_job_hash=upload_job_hash,
            ),
        ).prepare(),
        result_type=ApiResponseCancelFolderUploadJob,
    )


def api_storage_get_folder_config(
    folder_uuid: UUID,
    *,
    client: ApiClient,
) -> ApiStorageFolderConfig:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders/{folder_uuid}/folder-config".format(
                folder_uuid=folder_uuid,
            ),
        ).prepare(),
        result_type=ApiStorageFolderConfig,
    )


def api_storage_list_subfolders(
    folder_uuid: UUID,
    *,
    client: ApiClient,
    search: Union[None, str],
    is_recursive: Union[None, bool] = False,
    dataset_synced: Union[None, bool],
    include_hidden: Union[None, bool] = True,
    order: Union[None, ApiFoldersSortBy] = ApiFoldersSortBy.NAME,
    desc: Union[None, bool] = False,
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseStorageFolder:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders/{folder_uuid}/folders".format(
                folder_uuid=folder_uuid,
            ),
            params={
                k: v
                for k, v in {
                    "search": search,
                    "isRecursive": is_recursive,
                    "datasetSynced": dataset_synced,
                    "includeHidden": include_hidden,
                    "order": order,
                    "desc": desc,
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseStorageFolder,
    )


def api_storage_list_folder_groups(
    folder_uuid: UUID,
    *,
    client: ApiClient,
) -> ApiPaginatedResponseFolderGroup:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders/{folder_uuid}/groups".format(
                folder_uuid=folder_uuid,
            ),
        ).prepare(),
        result_type=ApiPaginatedResponseFolderGroup,
    )


def api_storage_add_folder_groups(
    folder_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestAddFolderGroups,
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/folders/{folder_uuid}/groups".format(
                folder_uuid=folder_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_storage_remove_folder_groups(
    folder_uuid: UUID,
    *,
    client: ApiClient,
    group_hash_list: List[UUID],
) -> None:
    return client.request(
        Request(
            method="delete",
            url="/v2/public/storage/folders/{folder_uuid}/groups".format(
                folder_uuid=folder_uuid,
            ),
            params={
                k: v
                for k, v in {
                    "groupHashList": group_hash_list,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=None,
    )


def api_storage_list_folder_items(
    folder_uuid: UUID,
    *,
    client: ApiClient,
    search: Union[None, str],
    is_recursive: Union[None, bool] = False,
    is_in_dataset: Union[None, bool],
    item_types: Union[List[ApiStorageItemType], None],
    order: Union[None, ApiFoldersSortBy] = ApiFoldersSortBy.NAME,
    desc: Union[None, bool] = False,
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
    sign_urls: Union[None, bool] = False,
) -> ApiPaginatedResponseStorageItem:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders/{folder_uuid}/items".format(
                folder_uuid=folder_uuid,
            ),
            params={
                k: v
                for k, v in {
                    "search": search,
                    "isRecursive": is_recursive,
                    "isInDataset": is_in_dataset,
                    "itemTypes": item_types,
                    "order": order,
                    "desc": desc,
                    "pageToken": page_token,
                    "pageSize": page_size,
                    "signUrls": sign_urls,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseStorageItem,
    )


def api_storage_delete_folder_items(
    folder_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestDeleteFolderChildren,
) -> ApiResponseDeletion:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/folders/{folder_uuid}/items/delete".format(
                folder_uuid=folder_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseDeletion,
    )


def api_storage_move_folder_items(
    folder_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestMoveItems,
) -> None:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/folders/{folder_uuid}/items/move".format(
                folder_uuid=folder_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=None,
    )


def api_storage_update_folder_item(
    folder_uuid: UUID,
    item_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestPatchItem,
) -> ApiResponseStorageItem:
    return client.request(
        Request(
            method="patch",
            url="/v2/public/storage/folders/{folder_uuid}/items/{item_uuid}".format(
                folder_uuid=folder_uuid,
                item_uuid=item_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiResponseStorageItem,
    )


def api_storage_list_item_children(
    folder_uuid: UUID,
    item_uuid: UUID,
    *,
    client: ApiClient,
    frames: Union[List[int], None],
    sign_urls: Union[None, bool] = False,
) -> ApiPaginatedResponseStorageItem:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders/{folder_uuid}/items/{item_uuid}/child-items".format(
                folder_uuid=folder_uuid,
                item_uuid=item_uuid,
            ),
            params={
                k: v
                for k, v in {
                    "frames": frames,
                    "signUrls": sign_urls,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseStorageItem,
    )


def api_storage_get_item_summary(
    folder_uuid: UUID,
    item_uuid: UUID,
    *,
    client: ApiClient,
) -> ApiResponseStorageItemSummary:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders/{folder_uuid}/items/{item_uuid}/summary".format(
                folder_uuid=folder_uuid,
                item_uuid=item_uuid,
            ),
        ).prepare(),
        result_type=ApiResponseStorageItemSummary,
    )


def api_storage_get_folder_summary(
    folder_uuid: UUID,
    *,
    client: ApiClient,
) -> ApiResponseStorageFolderSummary:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/folders/{folder_uuid}/summary".format(
                folder_uuid=folder_uuid,
            ),
        ).prepare(),
        result_type=ApiResponseStorageFolderSummary,
    )


def api_storage_create_upload_urls(
    folder_uuid: UUID,
    *,
    client: ApiClient,
    body: ApiRequestUploadSignedUrls,
) -> ApiPaginatedResponseUploadUrl:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/folders/{folder_uuid}/upload-signed-urls".format(
                folder_uuid=folder_uuid,
            ),
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiPaginatedResponseUploadUrl,
    )


def api_storage_get_items_bulk(
    *,
    client: ApiClient,
    body: ApiRequestGetItemsBulk,
) -> ApiPaginatedResponseStorageItem:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/items/get-bulk",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiPaginatedResponseStorageItem,
    )


def api_storage_migrate_items(
    *,
    client: ApiClient,
    body: ApiRequestStorageItemsMigrate,
) -> List[UUID]:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/items/migrate-storage",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=List[UUID],
    )


def api_storage_update_items_bulk(
    *,
    client: ApiClient,
    body: ApiRequestPatchItemsBulk,
) -> ApiPaginatedResponseStorageItem:
    return client.request(
        Request(
            method="patch",
            url="/v2/public/storage/items/patch-bulk",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=ApiPaginatedResponseStorageItem,
    )


def api_storage_start_item_reencoding(
    *,
    client: ApiClient,
    body: ApiRequestStorageItemsRencode,
) -> UUID:
    return client.request(
        Request(
            method="post",
            url="/v2/public/storage/items/reencode",
            json=client.serialise_payload(body),
        ).prepare(),
        result_type=UUID,
    )


def api_storage_get_reencoding_status(
    process_hash: UUID,
    *,
    client: ApiClient,
) -> ApiJobStatusInfo:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/items/reencode/{process_hash}".format(
                process_hash=process_hash,
            ),
        ).prepare(),
        result_type=ApiJobStatusInfo,
    )


def api_storage_get_item_info(
    item_uuid: UUID,
    *,
    client: ApiClient,
    sign_url: Union[None, bool] = False,
) -> ApiResponseStorageItem:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/items/{item_uuid}".format(
                item_uuid=item_uuid,
            ),
            params={
                k: v
                for k, v in {
                    "signUrl": sign_url,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiResponseStorageItem,
    )


def api_storage_search_folders(
    *,
    client: ApiClient,
    search: Union[None, str],
    dataset_synced: Union[None, bool],
    include_org_access: Union[None, bool],
    order: Union[None, ApiFoldersSortBy] = ApiFoldersSortBy.NAME,
    desc: Union[None, bool] = False,
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
) -> ApiPaginatedResponseStorageFolder:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/search/folders",
            params={
                k: v
                for k, v in {
                    "search": search,
                    "datasetSynced": dataset_synced,
                    "includeOrgAccess": include_org_access,
                    "order": order,
                    "desc": desc,
                    "pageToken": page_token,
                    "pageSize": page_size,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseStorageFolder,
    )


def api_storage_search_items(
    *,
    client: ApiClient,
    search: Union[None, str],
    is_in_dataset: Union[None, bool],
    item_types: Union[List[ApiStorageItemType], None],
    include_org_access: Union[None, bool],
    order: Union[None, ApiFoldersSortBy] = ApiFoldersSortBy.NAME,
    desc: Union[None, bool] = False,
    page_token: Union[None, str],
    page_size: Union[None, int] = 100,
    sign_urls: Union[None, bool] = False,
) -> ApiPaginatedResponseStorageItem:
    return client.request(
        Request(
            method="get",
            url="/v2/public/storage/search/items",
            params={
                k: v
                for k, v in {
                    "search": search,
                    "isInDataset": is_in_dataset,
                    "itemTypes": item_types,
                    "includeOrgAccess": include_org_access,
                    "order": order,
                    "desc": desc,
                    "pageToken": page_token,
                    "pageSize": page_size,
                    "signUrls": sign_urls,
                }.items()
                if v is not None
            },
        ).prepare(),
        result_type=ApiPaginatedResponseStorageItem,
    )


def api_user_get_bearer_token(
    *,
    client: ApiClient,
) -> ApiResponseBearerToken:
    return client.request(
        Request(
            method="get",
            url="/v2/public/user/bearer-token",
        ).prepare(),
        result_type=ApiResponseBearerToken,
    )


def api_user_get_current_user(
    *,
    client: ApiClient,
) -> ApiResponseGetCurrentUser:
    return client.request(
        Request(
            method="get",
            url="/v2/public/user/current",
        ).prepare(),
        result_type=ApiResponseGetCurrentUser,
    )


def api_user_list_org_groups(
    *,
    client: ApiClient,
) -> ApiPaginatedResponseGroup:
    return client.request(
        Request(
            method="get",
            url="/v2/public/user/current-organisation/groups",
        ).prepare(),
        result_type=ApiPaginatedResponseGroup,
    )


def api_user_get_org_role(
    *,
    client: ApiClient,
) -> ApiOrganisationUserInfo:
    return client.request(
        Request(
            method="get",
            url="/v2/public/user/current-organisation/info",
        ).prepare(),
        result_type=ApiOrganisationUserInfo,
    )
