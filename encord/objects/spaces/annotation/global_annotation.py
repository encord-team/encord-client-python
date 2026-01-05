from __future__ import annotations

from typing import TYPE_CHECKING

from encord.exceptions import LabelRowError
from encord.objects.classification_instance import ClassificationInstance
from encord.objects.spaces.annotation.base_annotation import _AnnotationData, _ClassificationAnnotation

if TYPE_CHECKING:
    from encord.objects.spaces.base_space import Space


class _GlobalClassificationAnnotation(_ClassificationAnnotation):
    """
    Annotation class that holds a global annotation. It exists over an entire Space.
    For image, audio, text and html spaces, this is the only kind of classification annotation there is.
    For video space, this can be contrasted with the FrameClassificationAnnotation, where the classification exists on certain frames.
    """

    def __init__(self, space: Space, classification_instance: ClassificationInstance):
        super().__init__(space, classification_instance)

    @property
    def frame(self) -> int:
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
            raise LabelRowError("This global classification is not available on this space.")
