import datetime
from enum import Enum
from typing import (
    Dict,
    List,
    Optional,
)
from uuid import UUID

from encord.orm.base_dto import BaseDTO


class ModelsListOrderBy(str, Enum):
    CREATED_AT = "createdAt"
    TITLE = "title"


class FeaturesMappingFeatureType(str, Enum):
    BOUNDING_BOX = "boundingBox"
    CLASSIFICATION_OPTION = "classificationOption"
    POLYGON = "polygon"


class ModelType(str, Enum):
    CLASSIFICATION = "classification"
    OBJECT_DETECTION = "objectDetection"
    SEGMENTATION = "segmentation"


class ModelArchitecture(str, Enum):
    FASTER_RCNN = "fasterRcnn"
    MASK_RCNN = "maskRcnn"
    RESNET_101 = "resnet101"
    RESNET_152 = "resnet152"
    RESNET_18 = "resnet18"
    RESNET_34 = "resnet34"
    RESNET_50 = "resnet50"
    VGG_16 = "vgg16"
    VGG_19 = "vgg19"


class ModelTrainingStatus(str, Enum):
    DONE = "done"
    ERROR = "error"
    PENDING = "pending"


class ModelPretrainedWeightsType(str, Enum):
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


class ModelGroup(BaseDTO):
    created_at: datetime.datetime
    description: str
    features: List[str]
    model: ModelArchitecture
    model_uuid: UUID
    title: str
    type: ModelType


class ModelIteration(BaseDTO):
    batch_size: int
    created_at: datetime.datetime
    duration: int
    epochs: int
    loss_log: Dict
    training_uuid: UUID


class ModelCreateRequest(BaseDTO):
    features: List[str]
    model: ModelArchitecture
    title: str
    description: Optional[str]


class ModelUpdateRequest(BaseDTO):
    description: Optional[str]
    title: Optional[str]


class ModelsListRequest(BaseDTO):
    order_by: ModelsListOrderBy
    order_asc: bool
    query: Optional[str]
    page_token: Optional[str]


class ModelWithIterations(BaseDTO):
    model_group: ModelGroup
    model_iterations: List[ModelIteration]


class ModelTrainingRequest(BaseDTO):
    batch_size: int
    epochs: int
    features_mapping: Dict[UUID, Dict[str, List[str]]]
    labels_uuids: List[UUID]
    pretrained_training_uuid: Optional[UUID]
    pretrained_weights_type: Optional[ModelPretrainedWeightsType]


class ModelTrainingResponse(BaseDTO):
    result: Optional[ModelIteration] = None
    status: ModelTrainingStatus


class ModelIterationTrainingDataListRequest(BaseDTO):
    page_token: Optional[str]


class StorageItemType(str, Enum):
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


class ModelIterationTrainingData(BaseDTO):
    data_uuid: UUID
    dataset_title: str
    dataset_uuid: UUID
    file_title: str
    item_type: StorageItemType
    label_uuid: UUID
    project_title: str
    project_uuid: UUID


class ModelIterationPolicy(str, Enum):
    MANUAL_SELECTION = "manualSelection"
    USE_ALL = "useAll"
    USE_LATEST = "useLatest"


class OntologyFeature(BaseDTO):
    feature_node_uuid: str
    name: str
    type: FeaturesMappingFeatureType
    color: Optional[str]


class ProjectModel(BaseDTO):
    created_at: datetime.datetime
    iteration_policy: ModelIterationPolicy
    model_uuid: UUID
    project_model_uuid: UUID
    project_uuid: UUID
    features_mapping: Dict[str, OntologyFeature]


class ProjectModelAttachRequest(BaseDTO):
    features_mapping: Dict[str, str]
    iteration_policy: ModelIterationPolicy
    model_uuid: UUID
    training_uuids: Optional[List[UUID]]


class ProjectModelsListRequest(BaseDTO):
    page_token: Optional[str]


class ProjectModelWithIterations(BaseDTO):
    model_group: ModelGroup
    project_model: ProjectModel
    project_model_iterations: List[ModelIteration]


class ProjectModelUpdateRequest(BaseDTO):
    features_mapping: Dict[str, str]
    iteration_policy: ModelIterationPolicy
    training_uuids: Optional[List[UUID]]


class PredictionClassificationRequest(BaseDTO):
    conf_thresh: float
    data_uuid: Optional[UUID]
    data_base64: Optional[str]
    frame_range_from: Optional[int]
    frame_range_to: Optional[int]


class PredictionClassificationResultItem(BaseDTO):
    classification_uuid: UUID
    confidence: float
    created_at: datetime.datetime
    created_by: str
    feature_id_child: str
    feature_id_parent: str
    manual_annotation: bool
    name: str
    value: str


class PredictionClassificationResponse(BaseDTO):
    result: Dict[int, Optional[PredictionClassificationResultItem]]


class PredictionInstanceSegmentationRequest(BaseDTO):
    allocation_enabled: bool
    conf_thresh: float
    data_uuid: Optional[UUID]
    data_base64: Optional[str]
    frame_range_from: Optional[int]
    frame_range_to: Optional[int]
    iou_thresh: float
    rdp_thresh: Optional[float]


class PredictionInstanceSegmentationPolygonPoint(BaseDTO):
    x: float
    y: float


class PredictionInstanceSegmentationResultItem(BaseDTO):
    color: str
    confidence: float
    created_at: datetime.datetime
    created_by: str
    feature_id: str
    manual_annotation: bool
    name: str
    object_id: str
    value: str
    polygon: List[PredictionInstanceSegmentationPolygonPoint]


class PredictionInstanceSegmentationResponse(BaseDTO):
    result: Dict[int, List[PredictionInstanceSegmentationResultItem]]


class PredictionObjectDetectionRequest(BaseDTO):
    allocation_enabled: bool
    conf_thresh: float
    data_uuid: Optional[UUID]
    data_base64: Optional[str]
    frame_range_from: Optional[int]
    frame_range_to: Optional[int]
    iou_thresh: float


class PredictionObjectDetectionBoundingBox(BaseDTO):
    h: float
    w: float
    x: float
    y: float


class PredictionObjectDetectionResultItem(BaseDTO):
    color: str
    confidence: float
    created_at: datetime.datetime
    created_by: str
    feature_id: str
    manual_annotation: bool
    name: str
    object_id: str
    value: str
    bounding_box: PredictionObjectDetectionBoundingBox


class PredictionObjectDetectionResponse(BaseDTO):
    result: Dict[int, List[PredictionObjectDetectionResultItem]]
