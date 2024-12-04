import datetime
from enum import Enum, IntEnum
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Union,
)
from uuid import UUID

from encord.orm.base_dto import BaseDTO


class ApiAnnotationTaskAction(str, Enum):
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    CREATED = "CREATED"
    DELETED = "DELETED"
    INACTIVATED = "INACTIVATED"
    RELEASED = "RELEASED"
    REOPENED = "REOPENED"
    RESOLVED = "RESOLVED"
    SKIPPED = "SKIPPED"


class ApiClientMetadataSchemaTypeVariantHint(str, Enum):
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    NUMBER = "number"
    TEXT = "text"
    UUID = "uuid"
    VARCHAR = "varchar"


class ApiCordDataType(IntEnum):
    VALUE_0 = 0
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_6 = 6
    VALUE_7 = 7
    VALUE_8 = 8


class ApiDatasetUserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class ApiFoldersSortBy(str, Enum):
    CREATEDAT = "createdAt"
    NAME = "name"


class ApiJobStatus(str, Enum):
    DONE = "done"
    ERROR = "error"
    SUBMITTED = "submitted"


class ApiJournalActionTarget(str, Enum):
    DATASET = "dataset"
    FOLDER = "folder"
    GROUP = "group"
    ONTOLOGY = "ontology"
    ORGANISATION = "organisation"
    PROJECT = "project"


class ApiJournalActionType(str, Enum):
    ADDITEMS = "addItems"
    CHANGEPERMISSIONS = "changePermissions"
    CREATE = "create"
    DELETE = "delete"
    FOLDERCONFIG = "folderConfig"
    MOVE = "move"
    REMOVEITEMS = "removeItems"
    UNSYNCFOLDER = "unsyncFolder"
    UPDATE = "update"
    UPDATEITEMS = "updateItems"


class ApiLabelReviewTaskStatus(str, Enum):
    APPROVED = "APPROVED"
    NEW = "NEW"
    REJECTED = "REJECTED"
    REOPENED = "REOPENED"
    RESOLVED = "RESOLVED"


class ApiLongPollingStatus(str, Enum):
    CANCELLED = "CANCELLED"
    DONE = "DONE"
    ERROR = "ERROR"
    PENDING = "PENDING"


class ApiNumberFormat(str, Enum):
    F32 = "F32"
    F64 = "F64"


class ApiOntologyUserRole(IntEnum):
    VALUE_0 = 0
    VALUE_1 = 1


class ApiOrganisationUserRole(IntEnum):
    VALUE_0 = 0
    VALUE_1 = 1


class ApiProjectType(str, Enum):
    MANUAL_QA = "manual_qa"
    WORKFLOW = "workflow"


class ApiProjectUserRole(IntEnum):
    VALUE_0 = 0
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4


class ApiReviewApprovalStatus(str, Enum):
    APPROVED = "APPROVED"
    DELETED = "DELETED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class ApiReviewTaskAction(str, Enum):
    APPROVE = "APPROVE"
    CREATE = "CREATE"
    DELETE = "DELETE"
    INACTIVATE = "INACTIVATE"
    REJECT = "REJECT"
    REOPEN = "REOPEN"
    RESOLVE = "RESOLVE"


class ApiStorageItemType(str, Enum):
    AUDIO = "audio"
    DICOMFILE = "dicomFile"
    DICOMSERIES = "dicomSeries"
    IMAGE = "image"
    IMAGEGROUP = "imageGroup"
    IMAGESEQUENCE = "imageSequence"
    NIFTI = "nifti"
    PDF = "pdf"
    PLAINTEXT = "plainText"
    VIDEO = "video"


class ApiStorageLocation(IntEnum):
    VALUE_0 = 0
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5


class ApiStorageLocationName(str, Enum):
    AZURE = "azure"
    DIRECTACCESS = "directAccess"
    ENCORD = "encord"
    GCP = "gcp"
    OPENTELEKOM = "openTelekom"
    S3 = "s3"
    S3COMPATIBLE = "s3Compatible"


class ApiStorageUserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class ApiTimersGroupBy(str, Enum):
    DATAUNIT = "dataUnit"
    PROJECT = "project"


class ApiTms1DisplayStatus(str, Enum):
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    DELETED = "DELETED"
    IN_REVIEW = "IN_REVIEW"
    QUEUED = "QUEUED"
    RETURNED = "RETURNED"


class ApiTms1TaskStatus(str, Enum):
    APPROVED = "APPROVED"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    CREATED = "CREATED"
    DELETED = "DELETED"
    IN_REVIEW = "IN_REVIEW"
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"


class ApiUploadItemType(str, Enum):
    AUDIO = "audio"
    DICOMFILE = "dicomFile"
    IMAGE = "image"
    NIFTI = "nifti"
    VIDEO = "video"


class ApiWorkflowNodeType(str, Enum):
    AGENT = "AGENT"
    ANNOTATION = "ANNOTATION"
    CONSENSUS_ANNOTATION = "CONSENSUS_ANNOTATION"
    CONSENSUS_REVIEW = "CONSENSUS_REVIEW"
    DONE = "DONE"
    PERCENTAGE_ROUTER = "PERCENTAGE_ROUTER"
    REVIEW = "REVIEW"
    START = "START"
    USER_ROUTER = "USER_ROUTER"


class ApiAgentNodeNodeType(str, Enum):
    AGENT = "AGENT"


class ApiAnnotationNodeNodeType(str, Enum):
    ANNOTATION = "ANNOTATION"


class ApiAnnotationTaskStateType(str, Enum):
    ANNOTATION = "ANNOTATION"


class ApiClientMetadataSchemaTypeBooleanTy(str, Enum):
    BOOLEAN = "boolean"


class ApiClientMetadataSchemaTypeDateTimeTy(str, Enum):
    DATETIME = "datetime"


class ApiClientMetadataSchemaTypeEmbeddingTy(str, Enum):
    EMBEDDING = "embedding"


class ApiClientMetadataSchemaTypeEnumTy(str, Enum):
    ENUM = "enum"


class ApiClientMetadataSchemaTypeNumberTy(str, Enum):
    NUMBER = "number"


class ApiClientMetadataSchemaTypeTextTy(str, Enum):
    TEXT = "text"


class ApiClientMetadataSchemaTypeTombstoneTy(str, Enum):
    TOMBSTONE = "tombstone"


class ApiClientMetadataSchemaTypeUUIDTy(str, Enum):
    UUID = "uuid"


class ApiClientMetadataSchemaTypeUserTy(str, Enum):
    USER = "user"


class ApiClientMetadataSchemaTypeVarCharTy(str, Enum):
    VARCHAR = "varchar"


class ApiClientMetadataSchemaTypeVariantTy(str, Enum):
    VARIANT = "variant"


class ApiConsensusAnnotationNodeNodeType(str, Enum):
    CONSENSUS_ANNOTATION = "CONSENSUS_ANNOTATION"


class ApiRequestDataUploadAudioExternalFileType(str, Enum):
    AUDIO = "AUDIO"


class ApiRequestDataUploadDicomSeriesExternalFileType(str, Enum):
    DICOM = "DICOM"


class ApiRequestDataUploadImageExternalFileType(str, Enum):
    IMAGE = "IMAGE"


class ApiRequestDataUploadImageGroupExternalFileType(str, Enum):
    IMG_GROUP = "IMG_GROUP"


class ApiRequestDataUploadImageGroupFromItemsExternalFileType(str, Enum):
    IMG_GROUP_FROM_ITEMS = "IMG_GROUP_FROM_ITEMS"


class ApiRequestDataUploadNiftiExternalFileType(str, Enum):
    NIFTI = "NIFTI"


class ApiRequestDataUploadPDFExternalFileType(str, Enum):
    PDF = "PDF"


class ApiRequestDataUploadTextExternalFileType(str, Enum):
    PLAIN_TEXT = "PLAIN_TEXT"


class ApiRequestDataUploadVideoExternalFileType(str, Enum):
    VIDEO = "VIDEO"


class ApiRequestLabelReviewApproveAction(str, Enum):
    APPROVE = "APPROVE"


class ApiRequestLabelReviewRejectAction(str, Enum):
    REJECT = "REJECT"


class ApiRequestLabelReviewReopenAction(str, Enum):
    REOPEN = "REOPEN"


class ApiRequestLabelReviewResolveAction(str, Enum):
    RESOLVE = "RESOLVE"


class ApiResponseGetTrainingResultDoneStatus(str, Enum):
    DONE = "DONE"


class ApiResponseGetTrainingResultErrorStatus(str, Enum):
    ERROR = "ERROR"


class ApiResponseGetTrainingResultPendingStatus(str, Enum):
    PENDING = "PENDING"


class ApiReviewNodeNodeType(str, Enum):
    REVIEW = "REVIEW"


class ApiReviewTaskStateType(str, Enum):
    REVIEW = "REVIEW"


class ApiAgentNode(BaseDTO):
    pathways_to_nodes_mapping: "ApiAgentNodePathwaysToNodesMapping"
    title: str
    uuid: UUID
    node_type: ApiAgentNodeNodeType = ApiAgentNodeNodeType.AGENT


class ApiAnnotationNode(BaseDTO):
    title: str
    to_node: UUID
    uuid: UUID
    node_type: ApiAnnotationNodeNodeType = ApiAnnotationNodeNodeType.ANNOTATION


class ApiAnnotationState(BaseDTO):
    action: ApiAnnotationTaskAction
    created_at: datetime.datetime
    priority: float
    task_uuid: UUID
    legacy_user_id: Union[None, int]
    task_metadata: Union["ApiAnnotationStateTaskMetadataType0", None]
    user_email: Union[None, str]
    user_hash: Union[None, str]


class ApiAnnotationTaskState(BaseDTO):
    graph_node: Union["ApiAgentNode", "ApiAnnotationNode", "ApiConsensusAnnotationNode"]
    outstanding_review_count: int
    resolvable_reviews: List["ApiReviewTaskState"]
    state: "ApiAnnotationState"
    task_created: datetime.datetime
    data_unit: Union["ApiTaskDataUnit", None]
    label_branch_name: Union[None, str]
    legacy_state_info: Union["ApiLegacyStateInfo", None]
    subtasks: Union[List["ApiAnnotationTaskState"], None]
    type: Union[None, ApiAnnotationTaskStateType] = ApiAnnotationTaskStateType.ANNOTATION


class ApiAutoSubfolderNamePlaceholder(BaseDTO):
    auto: Union[None, bool] = True
    suffix: Union[None, str]


ApiClientMetadataSchema = Dict


class ApiClientMetadataSchemaOrmRead(BaseDTO):
    created_at: datetime.datetime
    metadata_schema: "ApiClientMetadataSchemaOrmReadMetadataSchema"
    organisation_id: int
    updated_at: datetime.datetime
    uuid: UUID


class ApiClientMetadataSchemaTypeBoolean(BaseDTO):
    ty: Union[None, ApiClientMetadataSchemaTypeBooleanTy] = ApiClientMetadataSchemaTypeBooleanTy.BOOLEAN


class ApiClientMetadataSchemaTypeDateTime(BaseDTO):
    timezone: Union[None, str] = "UTC"
    ty: Union[None, ApiClientMetadataSchemaTypeDateTimeTy] = ApiClientMetadataSchemaTypeDateTimeTy.DATETIME


class ApiClientMetadataSchemaTypeEmbedding(BaseDTO):
    size: int
    ty: Union[None, ApiClientMetadataSchemaTypeEmbeddingTy] = ApiClientMetadataSchemaTypeEmbeddingTy.EMBEDDING


class ApiClientMetadataSchemaTypeEnum(BaseDTO):
    ty: Union[None, ApiClientMetadataSchemaTypeEnumTy] = ApiClientMetadataSchemaTypeEnumTy.ENUM
    values: Union[None, List[str]]


class ApiClientMetadataSchemaTypeNumber(BaseDTO):
    format_: Union[None, ApiNumberFormat] = ApiNumberFormat.F64
    ty: Union[None, ApiClientMetadataSchemaTypeNumberTy] = ApiClientMetadataSchemaTypeNumberTy.NUMBER


class ApiClientMetadataSchemaTypeText(BaseDTO):
    ty: Union[None, ApiClientMetadataSchemaTypeTextTy] = ApiClientMetadataSchemaTypeTextTy.TEXT


class ApiClientMetadataSchemaTypeTombstone(BaseDTO):
    deleted_ty: Union[
        "ApiClientMetadataSchemaTypeBoolean",
        "ApiClientMetadataSchemaTypeDateTime",
        "ApiClientMetadataSchemaTypeEmbedding",
        "ApiClientMetadataSchemaTypeEnum",
        "ApiClientMetadataSchemaTypeNumber",
        "ApiClientMetadataSchemaTypeText",
        "ApiClientMetadataSchemaTypeUUID",
        "ApiClientMetadataSchemaTypeUser",
        "ApiClientMetadataSchemaTypeVarChar",
        "ApiClientMetadataSchemaTypeVariant",
        None,
    ]
    ty: Union[None, ApiClientMetadataSchemaTypeTombstoneTy] = ApiClientMetadataSchemaTypeTombstoneTy.TOMBSTONE


class ApiClientMetadataSchemaTypeUUID(BaseDTO):
    ty: Union[None, ApiClientMetadataSchemaTypeUUIDTy] = ApiClientMetadataSchemaTypeUUIDTy.UUID


class ApiClientMetadataSchemaTypeUser(BaseDTO):
    ty: Union[None, ApiClientMetadataSchemaTypeUserTy] = ApiClientMetadataSchemaTypeUserTy.USER


class ApiClientMetadataSchemaTypeVarChar(BaseDTO):
    max_length: Union[None, int] = 8192
    ty: Union[None, ApiClientMetadataSchemaTypeVarCharTy] = ApiClientMetadataSchemaTypeVarCharTy.VARCHAR


class ApiClientMetadataSchemaTypeVariant(BaseDTO):
    hint: Union[None, ApiClientMetadataSchemaTypeVariantHint] = ApiClientMetadataSchemaTypeVariantHint.TEXT
    ty: Union[None, ApiClientMetadataSchemaTypeVariantTy] = ApiClientMetadataSchemaTypeVariantTy.VARIANT


class ApiConsensusAnnotationNode(BaseDTO):
    title: str
    to_node: UUID
    uuid: UUID
    node_type: ApiConsensusAnnotationNodeNodeType = ApiConsensusAnnotationNodeNodeType.CONSENSUS_ANNOTATION


class ApiCustomerProvidedAudioMetadata(BaseDTO):
    bit_depth: int
    codec: str
    duration: float
    file_size: int
    mime_type: str
    num_channels: int
    sample_rate: int


class ApiCustomerProvidedImageMetadata(BaseDTO):
    file_size: int
    height: int
    mime_type: str
    width: int


class ApiCustomerProvidedVideoMetadata(BaseDTO):
    duration: float
    file_size: int
    fps: float
    height: int
    mime_type: str
    width: int


class ApiDataUnitError(BaseDTO):
    action_description: str
    error: str
    object_urls: List[str]
    subtask_uuid: UUID


class ApiDataset(BaseDTO):
    backing_folder_uuid: Union[None, UUID]
    dataset_hash: UUID
    dataset_type: str
    description: str
    title: str


class ApiHTTPValidationError(BaseDTO):
    detail: Union[None, List["ApiValidationError"]]


class ApiIndexFolderConfig(BaseDTO):
    embedding_config: "ApiIndexFolderConfigEmbeddingConfig"
    base_metrics_enabled: Union[None, bool] = False


class ApiJobStatusInfo(BaseDTO):
    status: ApiJobStatus
    result: Union["ApiJobStatusInfoResultType1", List[Any], None]


class ApiJournalRecord(BaseDTO):
    action_data: Union["ApiJournalRecordActionDataType0", None]
    action_type: ApiJournalActionType
    created_at: datetime.datetime
    target_type: ApiJournalActionTarget
    target_uuid: UUID
    user_email: str
    uuid: UUID
    referenced_entity_uuid: Union[None, UUID]


class ApiLabelReview(BaseDTO):
    label_id: str
    label_type: str
    review_uuid: UUID
    status: ApiLabelReviewTaskStatus
    task_uuid: UUID


class ApiLabelValidationState(BaseDTO):
    branch_name: str
    errors: List[str]
    is_valid: bool
    label_hash: UUID
    version: int


class ApiLegacyStateInfo(BaseDTO):
    displayed_status: ApiTms1DisplayStatus
    status: ApiTms1TaskStatus


class ApiOrganisationUserInfo(BaseDTO):
    user_role: ApiOrganisationUserRole


class ApiPaginatedResponseDataset(BaseDTO):
    results: List["ApiDataset"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseDatasetGroup(BaseDTO):
    results: List["ApiResponseDatasetGroup"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseFolderGroup(BaseDTO):
    results: List["ApiResponseFolderGroup"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseGroup(BaseDTO):
    results: List["ApiResponseGroup"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseIndexCollection(BaseDTO):
    results: List["ApiResponseIndexCollection"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseIndexFilterPreset(BaseDTO):
    results: List["ApiResponseIndexFilterPreset"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseJournalRecord(BaseDTO):
    results: List["ApiJournalRecord"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseLabelReview(BaseDTO):
    results: List["ApiLabelReview"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseOntologyGroup(BaseDTO):
    results: List["ApiResponseOntologyGroup"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseProjectGroup(BaseDTO):
    results: List["ApiResponseProjectGroup"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseProjectPerformanceCollaboratorData(BaseDTO):
    results: List["ApiResponseProjectPerformanceCollaborator"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseProjectUser(BaseDTO):
    results: List["ApiProjectUser"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseStorageFolder(BaseDTO):
    results: List["ApiResponseStorageFolder"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseStorageItem(BaseDTO):
    results: List["ApiResponseStorageItem"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseStorageItemUnion(BaseDTO):
    results: List[Union["ApiResponseStorageItem", "ApiResponseStorageItemInaccessible"]]
    next_page_token: Union[None, str]


class ApiPaginatedResponseTask(BaseDTO):
    results: List["ApiTask"]
    next_page_token: Union[None, str]


class ApiPaginatedResponseUploadUrl(BaseDTO):
    results: List["ApiResponseUploadUrl"]


class ApiPathElement(BaseDTO):
    name: str
    uuid: UUID
    parent_uuid: Union[None, UUID]
    synced_dataset_hash: Union[None, UUID]


class ApiPerEmbeddingConfig(BaseDTO):
    advanced_metrics_enabled: Union[None, bool] = False
    embedding_reduction_enabled: Union[None, bool] = False


class ApiProject(BaseDTO):
    created_at: datetime.datetime
    description: str
    last_edited_at: datetime.datetime
    ontology_hash: UUID
    project_hash: UUID
    project_type: ApiProjectType
    title: str
    workflow: Union["ApiWorkflow", None]


class ApiProjectUser(BaseDTO):
    user_email: str
    user_role: ApiProjectUserRole


class ApiRequestAddDatasetGroups(BaseDTO):
    group_hash_list: List[UUID]
    user_role: ApiDatasetUserRole


class ApiRequestAddFolderGroups(BaseDTO):
    group_hash_list: List[UUID]
    user_role: ApiStorageUserRole


class ApiRequestAddOntologyGroups(BaseDTO):
    group_hash_list: List[UUID]
    user_role: ApiOntologyUserRole


class ApiRequestAddProjectGroup(BaseDTO):
    group_hash_list: List[UUID]
    user_role: ApiProjectUserRole


class ApiRequestCreateDataset(BaseDTO):
    create_backing_folder: bool
    legacy_call: bool
    title: str
    description: Union[None, str]


class ApiRequestCreateFolder(BaseDTO):
    name: str
    client_metadata: Union[None, str] = "{}"
    description: Union[None, str]
    parent: Union[None, UUID]


class ApiRequestDataUploadAudio(BaseDTO):
    object_url: str
    audio_metadata: Union["ApiCustomerProvidedAudioMetadata", None]
    client_metadata: Union[None, "ApiRequestDataUploadAudioClientMetadata"]
    external_file_type: Union[None, ApiRequestDataUploadAudioExternalFileType] = (
        ApiRequestDataUploadAudioExternalFileType.AUDIO
    )
    placeholder_item_uuid: Union[None, UUID]
    title: Union[None, str]


class ApiRequestDataUploadDicomSeries(BaseDTO):
    dicom_files: List["ApiRequestDataUploadDicomSeriesFile"]
    client_metadata: Union[None, "ApiRequestDataUploadDicomSeriesClientMetadata"]
    external_file_type: Union[None, ApiRequestDataUploadDicomSeriesExternalFileType] = (
        ApiRequestDataUploadDicomSeriesExternalFileType.DICOM
    )
    title: Union[None, str]


class ApiRequestDataUploadDicomSeriesFile(BaseDTO):
    url: str
    placeholder_item_uuid: Union[None, UUID]
    title: Union[None, str]


class ApiRequestDataUploadImage(BaseDTO):
    object_url: str
    client_metadata: Union[None, "ApiRequestDataUploadImageClientMetadata"]
    external_file_type: Union[None, ApiRequestDataUploadImageExternalFileType] = (
        ApiRequestDataUploadImageExternalFileType.IMAGE
    )
    image_metadata: Union["ApiCustomerProvidedImageMetadata", None]
    placeholder_item_uuid: Union[None, UUID]
    title: Union[None, str]


class ApiRequestDataUploadImageGroup(BaseDTO):
    images: List["ApiRequestDataUploadImageGroupImage"]
    client_metadata: Union[None, "ApiRequestDataUploadImageGroupClientMetadata"]
    cluster_by_resolution: Union[None, bool] = False
    create_video: Union[None, bool] = False
    external_file_type: Union[None, ApiRequestDataUploadImageGroupExternalFileType] = (
        ApiRequestDataUploadImageGroupExternalFileType.IMG_GROUP
    )
    title: Union[None, str]


class ApiRequestDataUploadImageGroupFromItems(BaseDTO):
    create_video: bool
    image_items: List[UUID]
    client_metadata: Union[None, "ApiRequestDataUploadImageGroupFromItemsClientMetadata"]
    cluster_by_resolution: Union[None, bool] = False
    external_file_type: Union[None, ApiRequestDataUploadImageGroupFromItemsExternalFileType] = (
        ApiRequestDataUploadImageGroupFromItemsExternalFileType.IMG_GROUP_FROM_ITEMS
    )
    title: Union[None, str]
    video_url_prefix: Union[None, str]


class ApiRequestDataUploadImageGroupImage(BaseDTO):
    url: str
    image_metadata: Union["ApiCustomerProvidedImageMetadata", None]
    placeholder_item_uuid: Union[None, UUID]
    title: Union[None, str]


class ApiRequestDataUploadItems(BaseDTO):
    audio: Union[None, List["ApiRequestDataUploadAudio"]]
    dicom_series: Union[None, List["ApiRequestDataUploadDicomSeries"]]
    image_groups: Union[None, List["ApiRequestDataUploadImageGroup"]]
    image_groups_from_items: Union[None, List["ApiRequestDataUploadImageGroupFromItems"]]
    images: Union[None, List["ApiRequestDataUploadImage"]]
    nifti: Union[None, List["ApiRequestDataUploadNifti"]]
    pdf: Union[None, List["ApiRequestDataUploadPDF"]]
    skip_duplicate_urls: Union[None, bool] = False
    text: Union[None, List["ApiRequestDataUploadText"]]
    upsert_metadata: Union[None, bool] = False
    videos: Union[None, List["ApiRequestDataUploadVideo"]]


class ApiRequestDataUploadNifti(BaseDTO):
    object_url: str
    client_metadata: Union[None, "ApiRequestDataUploadNiftiClientMetadata"]
    external_file_type: Union[None, ApiRequestDataUploadNiftiExternalFileType] = (
        ApiRequestDataUploadNiftiExternalFileType.NIFTI
    )
    placeholder_item_uuid: Union[None, UUID]
    title: Union[None, str]


class ApiRequestDataUploadPDF(BaseDTO):
    object_url: str
    client_metadata: Union[None, "ApiRequestDataUploadPDFClientMetadata"]
    external_file_type: Union[None, ApiRequestDataUploadPDFExternalFileType] = (
        ApiRequestDataUploadPDFExternalFileType.PDF
    )
    placeholder_item_uuid: Union[None, UUID]
    title: Union[None, str]


class ApiRequestDataUploadText(BaseDTO):
    object_url: str
    client_metadata: Union[None, "ApiRequestDataUploadTextClientMetadata"]
    external_file_type: Union[None, ApiRequestDataUploadTextExternalFileType] = (
        ApiRequestDataUploadTextExternalFileType.PLAIN_TEXT
    )
    placeholder_item_uuid: Union[None, UUID]
    title: Union[None, str]


class ApiRequestDataUploadVideo(BaseDTO):
    object_url: str
    client_metadata: Union[None, "ApiRequestDataUploadVideoClientMetadata"]
    external_file_type: Union[None, ApiRequestDataUploadVideoExternalFileType] = (
        ApiRequestDataUploadVideoExternalFileType.VIDEO
    )
    placeholder_item_uuid: Union[None, UUID]
    title: Union[None, str]
    video_metadata: Union["ApiCustomerProvidedVideoMetadata", None]


class ApiRequestDeleteFolderChildren(BaseDTO):
    child_uuids: List[UUID]
    remove_unused_frames: Union[None, bool] = False


class ApiRequestGetItemsBulk(BaseDTO):
    item_uuids: List[UUID]
    child_frame_numbers: Union[List[int], None]
    require_all: Union[None, bool] = False
    sign_urls: Union[None, bool] = False


class ApiRequestIndexCollectionBulkItem(BaseDTO):
    item_uuids: Union[None, List[UUID]]


class ApiRequestIndexCollectionInsert(BaseDTO):
    description: str
    name: str


class ApiRequestIndexCollectionPreset(BaseDTO):
    preset_uuid: UUID


class ApiRequestIndexCollectionUpdate(BaseDTO):
    description: Union[None, str]
    name: Union[None, str]


class ApiRequestIndexFilterPresetCreate(BaseDTO):
    description: str
    filter_preset_json: "ApiRequestIndexFilterPresetCreateFilterPresetJson"
    name: str


class ApiRequestIndexFilterPresetUpdate(BaseDTO):
    description: Union[None, str]
    filter_preset: Union["ApiRequestIndexFilterPresetUpdateFilterPresetType0", None]
    name: Union[None, str]


class ApiRequestLabelReviewApprove(BaseDTO):
    review_uuid: UUID
    action: Union[None, ApiRequestLabelReviewApproveAction] = ApiRequestLabelReviewApproveAction.APPROVE


class ApiRequestLabelReviewReject(BaseDTO):
    review_uuid: UUID
    action: Union[None, ApiRequestLabelReviewRejectAction] = ApiRequestLabelReviewRejectAction.REJECT


class ApiRequestLabelReviewReopen(BaseDTO):
    review_uuid: UUID
    action: Union[None, ApiRequestLabelReviewReopenAction] = ApiRequestLabelReviewReopenAction.REOPEN


class ApiRequestLabelReviewResolve(BaseDTO):
    review_uuid: UUID
    action: Union[None, ApiRequestLabelReviewResolveAction] = ApiRequestLabelReviewResolveAction.RESOLVE


class ApiRequestMoveFolders(BaseDTO):
    folder_uuids: List[UUID]
    new_parent_uuid: Union[None, UUID]


class ApiRequestMoveItems(BaseDTO):
    item_uuids: List[UUID]
    allow_synced_dataset_move: Union[None, bool] = False
    new_parent_uuid: Union[None, UUID]


class ApiRequestPatchFolder(BaseDTO):
    client_metadata: Union["ApiRequestPatchFolderClientMetadataType0", None]
    description: Union[None, str]
    name: Union[None, str]


class ApiRequestPatchFolderBulk(BaseDTO):
    folder_patches: Union[None, "ApiRequestPatchFolderBulkFolderPatches"]


class ApiRequestPatchItem(BaseDTO):
    client_metadata: Union["ApiRequestPatchItemClientMetadataType0", None]
    description: Union[None, str]
    name: Union[None, str]


class ApiRequestPatchItemsBulk(BaseDTO):
    item_patches: Union[None, "ApiRequestPatchItemsBulkItemPatches"]


class ApiRequestPriorities(BaseDTO):
    priorities: List[List[Union[UUID, float]]]


class ApiRequestStartTraining(BaseDTO):
    batch_size: int
    device: str
    epochs: int
    label_rows: List[UUID]
    model: str
    training_weights_link: Union[None, str]


class ApiRequestStorageItemsMigrate(BaseDTO):
    from_integration_hash: Union[None, UUID]
    items_map: Union[None, "ApiRequestStorageItemsMigrateItemsMap"]
    skip_missing: Union[None, bool] = False
    to_integration_hash: Union[None, UUID]
    urls_map: Union[None, "ApiRequestStorageItemsMigrateUrlsMap"]
    validate_access: Union[None, bool] = False


class ApiRequestStorageItemsRencode(BaseDTO):
    force_full_reencoding: bool
    process_title: str
    storage_items: List[UUID]


class ApiRequestUploadJob(BaseDTO):
    data_items: Union["ApiRequestDataUploadItems", None]
    external_files: Union["ApiRequestUploadJobExternalFilesType0", None]
    file_name: Union[None, str]
    ignore_errors: Union[None, bool] = False
    integration_hash: Union[None, UUID]


class ApiRequestUploadSignedUrls(BaseDTO):
    item_type: ApiUploadItemType
    count: Union[None, int] = 1
    frames_subfolder_name: Union["ApiAutoSubfolderNamePlaceholder", None, str]


class ApiResponseBearerToken(BaseDTO):
    token: str


class ApiResponseCancelFolderUploadJob(BaseDTO):
    units_cancelled_count: int


class ApiResponseCreateDataset(BaseDTO):
    backing_folder_uuid: Union[None, UUID]
    dataset_hash: UUID


class ApiResponseDatasetGroup(BaseDTO):
    created_at: datetime.datetime
    description: str
    group_hash: UUID
    is_same_organisation: bool
    name: str
    user_role: ApiDatasetUserRole


class ApiResponseDatasetShort(BaseDTO):
    data_hashes: List[UUID]
    data_units_created_at: datetime.datetime
    dataset_hash: UUID
    title: str
    backing_folder_uuid: Union[None, UUID]


class ApiResponseDatasetsWithUserRoles(BaseDTO):
    result: List["ApiResponseDatasetsWithUserRolesItem"]


class ApiResponseDatasetsWithUserRolesItem(BaseDTO):
    backing_folder_uuid: Union[None, UUID]
    created_at: datetime.datetime
    dataset_hash: UUID
    description: str
    last_edited_at: datetime.datetime
    storage_location: ApiStorageLocation
    title: str
    user_email: str
    user_hash: str
    user_role: ApiDatasetUserRole


class ApiResponseDeletion(BaseDTO):
    removed_folders_count: int
    removed_items_count: int


class ApiResponseFolderGroup(BaseDTO):
    created_at: datetime.datetime
    description: str
    group_hash: UUID
    is_same_organisation: bool
    name: str
    user_role: ApiStorageUserRole


class ApiResponseFolderUploadStatus(BaseDTO):
    errors: List[str]
    file_name: Union[None, str]
    items_with_names: List["ApiStorageItemWithName"]
    status: ApiLongPollingStatus
    unit_errors: List["ApiDataUnitError"]
    units_cancelled_count: int
    units_done_count: int
    units_error_count: int
    units_pending_count: int


class ApiResponseGetCurrentUser(BaseDTO):
    user_email: str
    user_hash: str


class ApiResponseGetTrainingResultDone(BaseDTO):
    result: "ApiResponseGetTrainingResultDoneData"
    status: Union[None, ApiResponseGetTrainingResultDoneStatus] = ApiResponseGetTrainingResultDoneStatus.DONE


class ApiResponseGetTrainingResultDoneData(BaseDTO):
    batch_size: int
    created_at: datetime.datetime
    duration: int
    epochs: int
    final_loss: float
    framework: str
    model: str
    model_hash: UUID
    title: str
    training_hash: UUID
    type: str
    weights_link: str


class ApiResponseGetTrainingResultError(BaseDTO):
    status: Union[None, ApiResponseGetTrainingResultErrorStatus] = ApiResponseGetTrainingResultErrorStatus.ERROR


class ApiResponseGetTrainingResultPending(BaseDTO):
    status: Union[None, ApiResponseGetTrainingResultPendingStatus] = ApiResponseGetTrainingResultPendingStatus.PENDING


class ApiResponseGroup(BaseDTO):
    created_at: datetime.datetime
    description: str
    group_hash: UUID
    name: str


class ApiResponseIndexCollection(BaseDTO):
    created_at: datetime.datetime
    description: str
    last_edited_at: datetime.datetime
    name: str
    top_level_folder_uuid: UUID
    uuid: UUID


class ApiResponseIndexCollectionBulkItem(BaseDTO):
    failed_items: List[UUID]


class ApiResponseIndexFilterPreset(BaseDTO):
    created_at: datetime.datetime
    description: str
    last_updated_at: datetime.datetime
    name: str
    uuid: UUID


class ApiResponseItemShort(BaseDTO):
    item_type: ApiStorageItemType
    name: str
    parent_name: str
    parent_uuid: UUID
    uuid: UUID


ApiResponseLegacyPublic = Dict


class ApiResponseOntologyGroup(BaseDTO):
    created_at: datetime.datetime
    description: str
    group_hash: UUID
    is_same_organisation: bool
    name: str
    user_role: ApiOntologyUserRole


class ApiResponseProjectGroup(BaseDTO):
    created_at: datetime.datetime
    description: str
    group_hash: UUID
    is_same_organisation: bool
    name: str
    user_role: ApiProjectUserRole


class ApiResponseProjectPerformanceCollaborator(BaseDTO):
    time_seconds: float
    user_email: str
    user_role: int
    data_title: Union[None, str]


class ApiResponseStorageFolder(BaseDTO):
    created_at: datetime.datetime
    description: str
    last_edited_at: datetime.datetime
    name: str
    owner: str
    user_role: ApiStorageUserRole
    uuid: UUID
    client_metadata: Union[None, str] = "{}"
    parent: Union[None, UUID]
    path_to_root: Union[List["ApiPathElement"], None]
    synced_dataset_hash: Union[None, UUID]


class ApiResponseStorageFolderSummary(BaseDTO):
    audios: int
    dicom_files: int
    dicom_series: int
    files: int
    folders: int
    image_groups: int
    image_sequences: int
    images: int
    niftis: int
    pdfs: int
    plain_texts: int
    tombstones: int
    total_size: float
    upload_jobs: int
    videos: int


class ApiResponseStorageItem(BaseDTO):
    backed_data_units_count: int
    created_at: datetime.datetime
    description: str
    item_type: ApiStorageItemType
    last_edited_at: datetime.datetime
    name: str
    owner: str
    parent: UUID
    storage_location: ApiStorageLocationName
    uuid: UUID
    audio_bit_depth: Union[None, int]
    audio_codec: Union[None, str]
    audio_num_channels: Union[None, int]
    audio_sample_rate: Union[None, int]
    child_frame_number: Union[None, int]
    client_metadata: Union[None, str] = "{}"
    dicom_instance_uid: Union[None, str]
    dicom_series_uid: Union[None, str]
    dicom_study_uid: Union[None, str]
    duration: Union[None, float]
    file_size: Union[None, int]
    fps: Union[None, float]
    frame_count: Union[None, int]
    height: Union[None, int]
    integration_hash: Union[None, UUID]
    is_placeholder: Union[None, bool] = False
    is_tombstone: Union[None, bool] = False
    mime_type: Union[None, str]
    signed_url: Union[None, str]
    url: Union[None, str]
    width: Union[None, int]


class ApiResponseStorageItemInaccessible(BaseDTO):
    uuid: UUID


class ApiResponseStorageItemSummary(BaseDTO):
    accessible_datasets: List["ApiResponseDatasetShort"]
    accessible_group_items: List["ApiResponseItemShort"]
    frame_in_groups: int
    used_in_datasets: int


class ApiResponseUploadUrl(BaseDTO):
    item_uuid: UUID
    object_key: str
    signed_url: str


class ApiReviewNode(BaseDTO):
    on_approve_to_node: UUID
    on_reject_to_node: UUID
    title: str
    uuid: UUID
    node_type: ApiReviewNodeNodeType = ApiReviewNodeNodeType.REVIEW


class ApiReviewState(BaseDTO):
    action: ApiReviewTaskAction
    created_at: datetime.datetime
    legacy_approval: ApiReviewApprovalStatus
    task_uuid: UUID
    legacy_user_email: Union[None, str]
    legacy_user_id: Union[None, int]
    task_metadata: Union["ApiReviewStateTaskMetadataType0", None]


class ApiReviewTaskState(BaseDTO):
    composite_review_task_uuid: UUID
    granularity: str
    granularity_hash: str
    graph_node: "ApiReviewNode"
    state: "ApiReviewState"
    task_created: datetime.datetime
    data_unit: Union["ApiTaskDataUnit", None]
    legacy_state_info: Union["ApiLegacyStateInfo", None]
    type: Union[None, ApiReviewTaskStateType] = ApiReviewTaskStateType.REVIEW


class ApiStorageFolderConfig(BaseDTO):
    index_folder_config: "ApiIndexFolderConfig"


class ApiStorageItemWithName(BaseDTO):
    item_uuid: UUID
    name: str


class ApiTask(BaseDTO):
    created_at: datetime.datetime
    updated_at: datetime.datetime
    uuid: UUID


class ApiTaskDataUnit(BaseDTO):
    data_cord_type: ApiCordDataType
    data_hash: str
    data_title: str
    dataset_hash: str
    dataset_title: str
    project_hash: str


class ApiValidationError(BaseDTO):
    loc: List[Union[int, str]]
    msg: str
    type: str


class ApiWorkflow(BaseDTO):
    stages: List["ApiWorkflowStage"]


class ApiWorkflowStage(BaseDTO):
    stage_type: ApiWorkflowNodeType
    title: str
    uuid: UUID


ApiAgentNodePathwaysToNodesMapping = Dict
ApiAnnotationStateTaskMetadataType0 = Dict
ApiClientMetadataSchemaOrmReadMetadataSchema = Dict
ApiIndexFolderConfigEmbeddingConfig = Dict
ApiJobStatusInfoResultType1 = Dict
ApiJournalRecordActionDataType0 = Dict
ApiRequestDataUploadAudioClientMetadata = Dict
ApiRequestDataUploadDicomSeriesClientMetadata = Dict
ApiRequestDataUploadImageClientMetadata = Dict
ApiRequestDataUploadImageGroupClientMetadata = Dict
ApiRequestDataUploadImageGroupFromItemsClientMetadata = Dict
ApiRequestDataUploadNiftiClientMetadata = Dict
ApiRequestDataUploadPDFClientMetadata = Dict
ApiRequestDataUploadTextClientMetadata = Dict
ApiRequestDataUploadVideoClientMetadata = Dict
ApiRequestIndexFilterPresetCreateFilterPresetJson = Dict
ApiRequestIndexFilterPresetUpdateFilterPresetType0 = Dict
ApiRequestPatchFolderClientMetadataType0 = Dict
ApiRequestPatchFolderBulkFolderPatches = Dict
ApiRequestPatchItemClientMetadataType0 = Dict
ApiRequestPatchItemsBulkItemPatches = Dict
ApiRequestStorageItemsMigrateItemsMap = Dict
ApiRequestStorageItemsMigrateUrlsMap = Dict
ApiRequestUploadJobExternalFilesType0 = Dict
ApiReviewStateTaskMetadataType0 = Dict
LegacyPublicRouteData = Dict
LegacyPublicUserRouteData = Dict
IndexGetPresetFilterResponsePublicIndexGetPresetFilterIndexPresetsUuidGet = Dict
OrgCreateMetadataSchemaLegacyMetadataSchema = Dict
WorkflowExecuteStageActionsBodyItem = Dict
