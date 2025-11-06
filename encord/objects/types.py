from __future__ import annotations

from typing import List, TypedDict, Union


class Answer(TypedDict):
    name: str
    value: str
    featureHash: str


class ClassificationObject(TypedDict):
    name: str
    value: str
    answers: Union[List[Answer], str, float]
    featureHash: str
    manualAnnotation: bool


class ClassificationAnswer(TypedDict):
    classificationHash: str
    featureHash: str
    classifications: List[ClassificationObject]
    range: Union[List[List[int]], None]

    # The values below are only guaranteed for non-geometric files
    confidence: Union[float, None]
    createdAt: Union[str, None]
    createdBy: Union[str, None]
    lastEditedAt: Union[str, None]
    lastEditedBy: Union[str, None]
    manualAnnotation: Union[bool, None]

    reviews: Union[List, None]
    """The reviews field is deprecated and soon to be removed"""


def is_containing_metadata(answer: ClassificationAnswer) -> bool:
    """Check if the classification answer contains necessary metadata fields."""
    return answer.get("createdBy") is not None
