from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence, Union, Iterable

from encord.objects import ClassificationInstance
from encord.objects.answers import NumericAnswerValue
from encord.objects.attributes import Attribute
from encord.objects.constants import DEFAULT_MANUAL_ANNOTATION
from encord.objects.ontology_object_instance import AnswersForFrames

if TYPE_CHECKING:
    from encord.objects import LabelRowV2, ObjectInstance, Option


class Entity:
    def __init__(self, label_row: LabelRowV2, ontology_instance: ObjectInstance | ClassificationInstance):
        self._entity_instance = ontology_instance
        self._label_row = label_row

    @property
    def entity_hash(self) -> str:
        if isinstance(self._entity_instance, ClassificationInstance):
            return self._entity_instance.classification_hash
        else:
            return self._entity_instance.object_hash

    def set_answer(
            self,
            answer: Union[str, NumericAnswerValue, Option, Sequence[Option]],
            attribute: Optional[Attribute] = None,
            overwrite: bool = False,
            manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
    ):
        self._entity_instance.set_answer(answer=answer, attribute=attribute, frames=None, overwrite=overwrite, manual_annotation=manual_annotation)

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, NumericAnswerValue, Option, Iterable[Option], None] = None,
        filter_frame: Optional[int] = None,
        is_dynamic: Optional[bool] = None,
    ) -> Union[str, NumericAnswerValue, Option, Iterable[Option], AnswersForFrames, None]:
        return self._entity_instance.get_answer(
            attribute=attribute,
            filter_answer=filter_answer,
            filter_frame=filter_frame,
            is_dynamic=is_dynamic,
        )
