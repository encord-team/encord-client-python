from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from encord.exceptions import LabelRowError
from encord.objects.coordinates import HtmlCoordinates
from encord.objects.html_node import HtmlRange, HtmlRanges
from encord.objects.spaces.annotation.base_annotation import (
    _AnnotationData,
    _ClassificationAnnotation,
    _ObjectAnnotation,
)

if TYPE_CHECKING:
    from encord.objects import ClassificationInstance, ObjectInstance
    from encord.objects.spaces.html_space import HTMLSpace


@dataclass
class _HtmlAnnotationData(_AnnotationData):
    """Annotation Data for HTML-based objects. Contains HtmlRanges."""

    ranges: HtmlRanges


class _HtmlObjectAnnotation(_ObjectAnnotation):
    """Annotations for HTML modality with XPath-based coordinates."""

    def __init__(self, space: HTMLSpace, object_instance: ObjectInstance):
        super().__init__(space, object_instance)
        self._space: HTMLSpace = space

    @property
    def frame(self) -> int:
        """This field is deprecated. It is only here for backwards compatibility. It always returns 0."""
        return 0

    @property
    def ranges(self) -> HtmlRanges:
        self._check_if_annotation_is_valid()
        return self._get_annotation_data().ranges

    @ranges.setter
    def ranges(self, ranges: Union[HtmlRange, HtmlRanges]) -> None:
        self._check_if_annotation_is_valid()
        if isinstance(ranges, HtmlRange):
            ranges = [ranges]

        self._space._object_hash_to_html_ranges[self._object_instance.object_hash] = ranges

    @property
    def coordinates(self) -> HtmlCoordinates:
        """Get the HTML coordinates for this annotation.

        Returns:
            HtmlCoordinates: The XPath-based coordinates for this annotation.
        """
        self._check_if_annotation_is_valid()
        html_ranges = self._space._object_hash_to_html_ranges[self._object_instance.object_hash]
        return HtmlCoordinates(range=html_ranges)

    @coordinates.setter
    def coordinates(self, coordinates: HtmlCoordinates) -> None:
        """Set the HTML coordinates for this annotation.

        Args:
            coordinates: The new HtmlCoordinates to set.
        """
        self._check_if_annotation_is_valid()
        self._space._object_hash_to_html_ranges[self._object_instance.object_hash] = coordinates.range

    def _get_annotation_data(self) -> _HtmlAnnotationData:
        return _HtmlAnnotationData(
            annotation_metadata=self._object_instance._instance_metadata,
            ranges=self._space._object_hash_to_html_ranges[self._object_instance.object_hash],
        )

    def _check_if_annotation_is_valid(self) -> None:
        if self._object_instance.object_hash not in self._space._object_hash_to_html_ranges:
            raise LabelRowError(
                "Trying to use an HtmlObjectAnnotation for an ObjectInstance that is not on this space."
            )


class _HtmlClassificationAnnotation(_ClassificationAnnotation):
    """Classification annotations for HTML modality."""

    def __init__(self, space: HTMLSpace, classification_instance: ClassificationInstance):
        super().__init__(space, classification_instance)  # type: ignore[arg-type]
        self._space: HTMLSpace = space  # type: ignore[assignment]

    @property
    def frame(self) -> int:
        """This field is deprecated. It is only here for backwards compatibility. It always returns 0."""
        return 0

    def _get_annotation_data(self) -> _AnnotationData:
        return self._space._global_classification_hash_to_annotation_data[
            self._classification_instance.classification_hash
        ]

    def _check_if_annotation_is_valid(self) -> None:
        if (
            self._classification_instance.classification_hash
            not in self._space._global_classification_hash_to_annotation_data
        ):
            raise LabelRowError("This annotation is not available on this space.")
