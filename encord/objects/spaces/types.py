from typing import Any, TypedDict


class FrameAnnotationIndex(TypedDict):
    classifications: list[dict[str, Any]]


class FrameClassificationIndex(FrameAnnotationIndex):
    classificationHash: str
    featureHash: str


class FrameObjectIndex(FrameAnnotationIndex):
    objectHash: str
