from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from encord.objects.common import Shape

""" Typed Dicts for Shape Coordinates """


class BoundingBoxDict(TypedDict):
    h: float
    w: float
    x: float
    y: float


class BoundingBoxFrameCoordinatesDict(TypedDict):
    boundingBox: BoundingBoxDict


class PointDict(TypedDict):
    x: float
    y: float


class PointFrameCoordinatesDict(TypedDict):
    point: dict[str, PointDict]  # Actually the key here is always '0', but no way to type that.


class PointDict3D(PointDict):
    z: float


class Point3DFrameCoordinatesDict(TypedDict):
    point: dict[str, PointDict3D]  # Actually the key here is always '0', but no way to type that.


class RotatableBoundingBoxDict(BoundingBoxDict):
    theta: float


class RotatableBoundingBoxFrameCoordinatesDict(TypedDict):
    rotatableBoundingBox: RotatableBoundingBoxDict


PolylineDict = Union[Dict[str, PointDict], list[PointDict], Dict[str, PointDict3D], list[PointDict3D]]


class PolylineFrameCoordinatesDict(TypedDict):
    polyline: PolylineDict


LegacyPolygonDict = Union[Dict[str, PointDict], list[PointDict]]
PolygonDict = List[List[List[float]]]  # Introduced to support complex polygons


class PolygonFrameCoordinatesDictRequired(TypedDict):
    polygon: LegacyPolygonDict


class PolygonFrameCoordinatesDict(PolygonFrameCoordinatesDictRequired, total=False):
    polygons: Optional[PolygonDict]  # This was introduced to support complex polygons.


class AnswerDict(TypedDict):
    """
    Answer for attributes/classifications.
    """

    name: str
    value: str
    featureHash: str


class BaseFrameObjectRequired(TypedDict):
    """
    Required fields for frame object in label blob.
    """

    objectHash: str
    featureHash: str
    name: str
    color: str
    value: str
    createdAt: str


class BaseFrameObject(BaseFrameObjectRequired, total=False):
    """
    All fields for base frame object in label blob.
    Shape data is not included here.
    """

    createdBy: Optional[str]  # This is optional because we set the default to the current user on the BE
    lastEditedBy: Optional[str]  # This is optional because we set the default to the current user on the BE
    lastEditedAt: str
    confidence: float
    manualAnnotation: bool
    reviews: list[Any]  # TODO: Remove this as its deprecated
    isDeleted: bool  # TODO: Remove this as its deprecated, although its still being sent out


class BoundingBoxFrameObject(BaseFrameObject, BoundingBoxFrameCoordinatesDict):
    shape: Literal[Shape.BOUNDING_BOX]


class RotatableBoundingBoxFrameObject(BaseFrameObject, RotatableBoundingBoxFrameCoordinatesDict):
    shape: Literal[Shape.ROTATABLE_BOUNDING_BOX]


class PolygonFrameObject(BaseFrameObject, PolygonFrameCoordinatesDict):
    shape: Literal[Shape.POLYGON]


class PolylineFrameObject(BaseFrameObject, PolylineFrameCoordinatesDict):
    shape: Literal[Shape.POLYLINE]


class PointFrameObject2D(BaseFrameObject, PointFrameCoordinatesDict):
    shape: Literal[Shape.POINT]


class PointFrameObject3D(BaseFrameObject, Point3DFrameCoordinatesDict):
    shape: Literal[Shape.POINT]


PointFrameObject = Union[PointFrameObject2D, PointFrameObject3D]

""" Frame object in the label blob. Contains shape data, and is differentiated by the 'shape' field. """
FrameObject = Union[
    BoundingBoxFrameObject, RotatableBoundingBoxFrameObject, PolygonFrameObject, PointFrameObject, PolylineFrameObject
]


class FrameClassificationRequired(TypedDict):
    classificationHash: str
    featureHash: str
    name: str
    value: str


class FrameClassification(FrameClassificationRequired, total=False):
    """
    Frame classification in label blob.
    No answers here, they are in the ClassificationAnswer
    """

    confidence: float
    createdAt: str
    createdBy: Optional[str]  # This can be optional because we set the default to current the user at the BE
    lastEditedAt: str
    lastEditedBy: str
    manualAnnotation: bool
    reviews: list[Any]


class LabelBlob(TypedDict):
    objects: list[FrameObject]
    classifications: list[FrameClassification]


class AttributeDict(TypedDict):
    """
    Attribute for a classification OR an object.
    Note that these are inappropriately called "classifications" in ObjectAnswer and ClassificationAnswer.
    """

    name: str
    value: str
    answers: Union[List[AnswerDict], str, float, int, None]
    featureHash: str
    manualAnnotation: bool


class DynamicAttributeObjectRequired(AttributeDict):
    """Required fields for dynamic attribute object in object_actions."""

    range: list[list[int]]
    dynamic: bool
    shouldPropagate: bool
    trackHash: Optional[str]  # See if we can remove this


class DynamicAttributeObject(DynamicAttributeObjectRequired, total=False):
    """All fields for dynamic attribute object in object_actions."""

    spaceId: str


class ClassificationAnswerRequired(TypedDict):
    classificationHash: str
    featureHash: str
    classifications: List[AttributeDict]


class ClassificationAnswer(ClassificationAnswerRequired, total=False):
    """Classification answer that contains attributes (sadly here its called classifications too) for the classification"""

    # The values below are only guaranteed for non-geometric files (e.g. Audio & Text)
    range: Union[List[List[int]], None]
    confidence: Union[float, None]
    createdAt: Union[str, None]
    createdBy: Union[str, None]
    lastEditedAt: Union[str, None]
    lastEditedBy: Union[str, None]
    manualAnnotation: Union[bool, None]
    reviews: list[Any]  # TODO: Remove this as its deprecated
    spaces: Union[Dict[str, SpaceRange], None]  # Only exists if item is on a space


class ObjectAnswerForGeometric(TypedDict):
    objectHash: str
    classifications: List[AttributeDict]


class SpaceRange(TypedDict):
    range: list[list[int]]


class ObjectAnswerForNonGeometric(BaseFrameObject):
    """For non-geometric modalities, metadata is contained in object answers, instead of frame"""

    shape: Union[Literal[Shape.TEXT], Literal[Shape.AUDIO]]
    classifications: List[AttributeDict]
    range: Union[List[List[int]], None]
    spaces: Dict[str, SpaceRange]  # Important for non-geometric shapes, where space info must live on ObjectAnswer


class ObjectAnswerForHtml(BaseFrameObject):
    shape: Literal[Shape.TEXT]
    classifications: List[AttributeDict]
    range_html: list[dict]
    range: Union[List[List[int]], None]


ObjectAnswer = Union[ObjectAnswerForGeometric, ObjectAnswerForNonGeometric, ObjectAnswerForHtml]


class ObjectAction(TypedDict):
    objectHash: str
    actions: List[DynamicAttributeObject]


class LabelRowDict(TypedDict, total=False):
    """Work in progress type definition of a label row"""

    label_hash: str
    branch_name: str
    created_at: str
    last_edited_at: str
    data_hash: str
    dataset_hash: str
    dataset_title: str
    data_title: str
    data_type: str
    annotation_task_status: str
    is_shadow_data: bool
    label_status: str
    object_actions: Dict
    object_answers: Dict
    classification_answers: Dict[str, ClassificationAnswer]
    data_units: Dict
    spaces: Dict


def _is_containing_metadata(answer: ClassificationAnswer) -> bool:
    """Check if the classification answer contains necessary metadata fields."""
    return "createdBy" in answer


def _is_containing_spaces(answer: ClassificationAnswer) -> bool:
    """Check if the classification answer contains spaces field."""
    return "spaces" in answer
