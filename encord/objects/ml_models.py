import datetime
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Union,
)
from uuid import UUID

from encord.orm.base_dto import BaseDTO


class ApiFeaturesMappingFeatureType(str, Enum):
    BOUNDING_BOX = "boundingBox"
    CLASSIFICATION_OPTION = "classificationOption"
    POLYGON = "polygon"


class ApiIterationPolicy(str, Enum):
    MANUAL_SELECTION = "manualSelection"
    USE_ALL = "useAll"
    USE_LATEST = "useLatest"


class ApiMlModelType(str, Enum):
    CLASSIFICATION = "classification"
    OBJECT_DETECTION = "objectDetection"
    SEGMENTATION = "segmentation"


class ApiModelArchitecture(str, Enum):
    FASTER_RCNN = "fasterRcnn"
    MASK_RCNN = "maskRcnn"
    RESNET101 = "resnet101"
    RESNET152 = "resnet152"
    RESNET18 = "resnet18"
    RESNET34 = "resnet34"
    RESNET50 = "resnet50"
    VGG16 = "vgg16"
    VGG19 = "vgg19"


class ApiPretrainedWeightsType(str, Enum):
    FASTER_RCNN_R101_C43X = "fasterRcnnR101C43X"
    FASTER_RCNN_R101_DC53X = "fasterRcnnR101Dc53X"
    FASTER_RCNN_R101_FPN3X = "fasterRcnnR101Fpn3X"
    FASTER_RCNN_R50_C41X = "fasterRcnnR50C41X"
    FASTER_RCNN_R50_C43X = "fasterRcnnR50C43X"
    FASTER_RCNN_R50_DC51X = "fasterRcnnR50Dc51X"
    FASTER_RCNN_R50_DC53X = "fasterRcnnR50Dc53X"
    FASTER_RCNN_R50_FPN1X = "fasterRcnnR50Fpn1X"
    FASTER_RCNN_R50_FPN3X = "fasterRcnnR50Fpn3X"
    FASTER_RCNN_X101_32X8D_FPN3X = "fasterRcnnX10132X8DFpn3X"
    MASK_RCNN_R101_FPN3X = "maskRcnnR101Fpn3X"
    MASK_RCNN_R50_C41X = "maskRcnnR50C41X"
    MASK_RCNN_R50_C43X = "maskRcnnR50C43X"
    MASK_RCNN_X101_32X8D_FPN3X = "maskRcnnX10132X8DFpn3X"


class ApiReadModelsOrderBy(str, Enum):
    CREATED_AT = "createdAt"
    TITLE = "title"


class ApiStorageItemType(str, Enum):
    AUDIO = "audio"
    DICOM_FILE = "dicomFile"
    DICOM_SERIES = "dicomSeries"
    IMAGE = "image"
    IMAGE_GROUP = "imageGroup"
    IMAGE_SEQUENCE = "imageSequence"
    NIFTI = "nifti"
    PDF = "pdf"
    PLAIN_TEXT = "plainText"
    VIDEO = "video"


class ApiResponseGetTrainingResultStatus(str, Enum):
    DONE = "done"
    ERROR = "error"
    PENDING = "pending"


class ApiModelGroup(BaseDTO):
    created_at: datetime.datetime
    description: str
    features: List[str]
    model: ApiModelArchitecture
    model_uuid: UUID
    title: str
    type: ApiMlModelType


class ApiModelIteration(BaseDTO):
    batch_size: int
    created_at: datetime.datetime
    duration: int
    epochs: int
    loss_log: Dict
    training_uuid: UUID


class ApiModelIterationTrainingDataItem(BaseDTO):
    data_uuid: UUID
    dataset_title: str
    dataset_uuid: UUID
    file_title: str
    item_type: ApiStorageItemType
    label_uuid: UUID
    project_title: str
    project_uuid: UUID


class ApiModelIterationTrainingData(BaseDTO):
    items: List[ApiModelIterationTrainingDataItem]


class ApiOntologyFeature(BaseDTO):
    feature_node_uuid: str
    name: str
    type: ApiFeaturesMappingFeatureType
    color: Union[None, str]


class ApiProjectModel(BaseDTO):
    created_at: datetime.datetime
    iteration_policy: ApiIterationPolicy
    model_uuid: UUID
    project_model_uuid: UUID
    project_uuid: UUID
    features_mapping: Dict[str, ApiOntologyFeature]


class ApiRequestClassificationPrediction(BaseDTO):
    conf_thresh: float
    data_uuid: UUID | None
    data_base64: str | None
    frame_range_from: int | None
    frame_range_to: int | None


class ApiRequestInstanceSegmentationPrediction(BaseDTO):
    allocation_enabled: bool
    conf_thresh: float
    data_uuid: UUID | None
    data_base64: str | None
    frame_range_from: int | None
    frame_range_to: int | None
    iou_thresh: float
    rdp_thresh: Union[None, float]


class ApiRequestModelAttachToProject(BaseDTO):
    features_mapping: Dict[str, str]
    iteration_policy: ApiIterationPolicy
    model_uuid: UUID
    training_uuids: Union[List[UUID], None]


class ApiRequestModelInsert(BaseDTO):
    features: List[str]
    model: ApiModelArchitecture
    title: str
    description: Union[None, str]


class ApiRequestModelOperationsTrain(BaseDTO):
    batch_size: int
    epochs: int
    features_mapping: Dict[UUID, Dict[str, list[str]]]
    labels_uuids: List[UUID]
    pretrained_training_uuid: Union[None, UUID]
    pretrained_weights_type: Union[ApiPretrainedWeightsType, None]


class ApiRequestModelPatch(BaseDTO):
    description: Union[None, str]
    title: Union[None, str]


class ApiRequestObjectDetectionPrediction(BaseDTO):
    allocation_enabled: bool
    conf_thresh: float
    data_uuid: UUID | None
    data_base64: str | None
    frame_range_from: int | None
    frame_range_to: int | None
    iou_thresh: float


class ApiRequestProjectModelUpdate(BaseDTO):
    features_mapping: Dict[str, str]
    iteration_policy: ApiIterationPolicy
    training_uuids: Union[List[UUID], None]


class ApiResponseGetTrainingResult(BaseDTO):
    result: ApiModelIteration | None = None
    status: ApiResponseGetTrainingResultStatus


class ApiResponseModelReadItem(BaseDTO):
    model_group: ApiModelGroup
    model_iterations: List[ApiModelIteration]


class ApiResponseModelRead(BaseDTO):
    models: List[ApiResponseModelReadItem]
    total_count: int


class ApiResponseProjectModelReadItem(BaseDTO):
    model_group: ApiModelGroup
    project_model: ApiProjectModel
    project_model_iterations: List[ApiModelIteration]


class ApiResponseProjectModelRead(BaseDTO):
    items: List[ApiResponseProjectModelReadItem]


class ApiResponseClassificationPredictionResultItem(BaseDTO):
    classification_uuid: UUID
    confidence: float
    created_at: datetime.datetime
    created_by: str
    feature_id_child: str
    feature_id_parent: str
    manual_annotation: bool
    name: str
    value: str


class ApiResponseClassificationPredictionResult(BaseDTO):
    result: dict[int, ApiResponseClassificationPredictionResultItem | None]


class ApiInstanceSegmentationPredictionPolygonItem(BaseDTO):
    x: float
    y: float


class ApiResponseInstanceSegmentationPredictionResultItem(BaseDTO):
    color: str
    confidence: float
    created_at: datetime.datetime
    created_by: str
    feature_id: str
    manual_annotation: bool
    name: str
    object_id: str
    polygon: List[ApiInstanceSegmentationPredictionPolygonItem]
    value: str


class ApiResponseInstanceSegmentationPredictionResult(BaseDTO):
    result: Dict[int, list[ApiResponseInstanceSegmentationPredictionResultItem]]


class ApiResponseObjectDetectionPredictionResultItemBoundingBox(BaseDTO):
    h: float
    w: float
    x: float
    y: float


class ApiResponseObjectDetectionPredictionResultItem(BaseDTO):
    bounding_box: ApiResponseObjectDetectionPredictionResultItemBoundingBox
    color: str
    confidence: float
    created_at: datetime.datetime
    created_by: str
    feature_id: str
    manual_annotation: bool
    name: str
    object_id: str
    value: str


class ApiResponseObjectDetectionPredictionResult(BaseDTO):
    result: Dict[int, list[ApiResponseObjectDetectionPredictionResultItem]]
