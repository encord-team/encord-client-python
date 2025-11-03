from __future__ import annotations

from collections.abc import Iterable as IterableABC
from typing import TYPE_CHECKING, Iterable, Optional, Sequence, Union

from encord.objects import ClassificationInstance
from encord.objects.answers import NumericAnswerValue
from encord.objects.attributes import Attribute
from encord.objects.constants import DEFAULT_MANUAL_ANNOTATION
from encord.objects.ontology_object_instance import AnswersForFrames

if TYPE_CHECKING:
    from encord.objects import LabelRowV2, ObjectInstance, Option
    from encord.objects.spaces.annotation.base_annotation import ObjectAnnotation
    from encord.objects.spaces.base_space import Space


class SpaceObject:
    def __init__(self, label_row: LabelRowV2, object_instance: ObjectInstance):
        self._object_instance = object_instance
        self._label_row = label_row
        self._space_map: dict[str, Space] = dict()

    @property
    def spaces(self) -> dict[str, Space]:
        return self._space_map

    @property
    def object_hash(self) -> str:
        return self._object_instance.object_hash

    def set_answer(
        self,
        answer: Union[str, NumericAnswerValue, Option, Sequence[Option]],
        attribute: Optional[Attribute] = None,
        overwrite: bool = False,
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
    ):
        self._object_instance.set_answer(
            answer=answer, attribute=attribute, frames=None, overwrite=overwrite, manual_annotation=manual_annotation
        )

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, NumericAnswerValue, Option, Iterable[Option], None] = None,
        filter_frame: Optional[int] = None,
        is_dynamic: Optional[bool] = None,
    ) -> Union[str, NumericAnswerValue, Option, Iterable[Option], AnswersForFrames, None]:
        return self._object_instance.get_answer(
            attribute=attribute,
            filter_answer=filter_answer,
            filter_frame=filter_frame,
            is_dynamic=is_dynamic,
        )

    def get_annotations(
        self, spaces: Optional[Union["Space", Iterable["Space"]]] = None
    ) -> list["ObjectAnnotation"]:
        """Get all annotations for this SpaceObject across the spaces it has been placed in.

        Args:
            spaces: Optional filter to limit results to specific space(s). Can be:
                - None: Get annotations from all spaces where this object is placed
                - A single Space instance: Get annotations only from that space
                - An iterable of Space instances: Get annotations only from those spaces

        Returns:
            A list of ObjectAnnotation instances representing all annotations for this object
            in the specified spaces. The annotation types may vary depending on the space type
            (e.g., TwoDimensionalObjectAnnotation, TwoDimensionalFrameObjectAnnotation, RangeObjectAnnotation).
        """
        # Determine which spaces to query
        spaces_to_query: Iterable["Space"]
        if spaces is None:
            # Get annotations from all spaces where this object is placed
            spaces_to_query = self._space_map.values()
        elif isinstance(spaces, IterableABC):
            # Iterable of spaces provided (list, tuple, set, etc.)
            # Strings are iterable but not what we want - treat as invalid
            if isinstance(spaces, str):
                raise TypeError(f"Expected Space or iterable of Spaces, got string: {spaces}")
            spaces_to_query = spaces
        else:
            # Not None and not iterable - must be a single Space instance
            spaces_to_query = [spaces]

        # Collect all annotations for this object from the specified spaces
        annotations: list["ObjectAnnotation"] = []
        for space in spaces_to_query:
            # Only query spaces where this object is actually placed
            if space.space_id not in self._space_map:
                continue

            # Get all object annotations from this space
            space_annotations = space.get_object_annotations()

            # Filter to only include annotations for this object
            for annotation in space_annotations:
                if annotation.object_hash == self.object_hash:
                    annotations.append(annotation)

        return annotations

    def _add_to_space(self, space: Space) -> None:
        self._space_map.update({space.space_id: space})

    def _remove_from_space(self, space: Space) -> None:
        self._space_map.pop(space.space_id)


class SpaceClassification:
    def __init__(self, label_row: LabelRowV2, classification_instance: ClassificationInstance):
        self._classification_instance = classification_instance
        self._label_row = label_row
        self._space_map: dict[str, Space] = dict()

    @property
    def spaces(self) -> dict[str, Space]:
        return self._space_map

    @property
    def classification_hash(self) -> str:
        return self._classification_instance.classification_hash

    def set_answer(
        self,
        answer: Union[str, NumericAnswerValue, Option, Sequence[Option]],
        attribute: Optional[Attribute] = None,
        overwrite: bool = False,
    ):
        self._classification_instance.set_answer(answer=answer, attribute=attribute, overwrite=overwrite)

    def get_answer(
        self,
        attribute: Attribute,
    ) -> Union[str, NumericAnswerValue, Option, Iterable[Option], AnswersForFrames, None]:
        return self._classification_instance.get_answer(
            attribute=attribute,
        )

    def _add_to_space(self, space: Space) -> None:
        self._space_map.update({space.space_id: space})

    def _remove_from_space(self, space: Space) -> None:
        self._space_map.pop(space.space_id)
