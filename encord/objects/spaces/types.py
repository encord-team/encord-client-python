from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict


class FrameAnnotationIndex(TypedDict):
    classifications: list[dict[str, Any]]


class FrameClassificationIndex(FrameAnnotationIndex):
    classificationHash: str
    featureHash: str


class FrameObjectIndex(FrameAnnotationIndex):
    objectHash: str


class AddObjectInstanceParams(TypedDict, total=False):
    created_at: Optional[datetime]
    created_by: Optional[str]
    last_edited_at: Optional[datetime]
    last_edited_by: Optional[str]
    confidence: Optional[float]
    manual_annotation: Optional[bool]
    reviews: Optional[List[Dict]]
    is_deleted: Optional[bool]
