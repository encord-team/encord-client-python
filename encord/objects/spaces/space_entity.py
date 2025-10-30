from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional, Sequence, Union

from encord.objects import ClassificationInstance
from encord.objects.answers import NumericAnswerValue
from encord.objects.attributes import Attribute
from encord.objects.constants import DEFAULT_MANUAL_ANNOTATION
from encord.objects.ontology_object_instance import AnswersForFrames

if TYPE_CHECKING:
    from encord.objects import LabelRowV2, ObjectInstance, Option
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
