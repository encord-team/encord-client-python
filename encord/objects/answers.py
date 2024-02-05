from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Iterable, List, NoReturn, Optional, Set, TypeVar

from encord.common.deprecated import deprecated
from encord.objects.attributes import (
    Attribute,
    ChecklistAttribute,
    RadioAttribute,
    TextAttribute,
)
from encord.objects.constants import DEFAULT_MANUAL_ANNOTATION
from encord.objects.frames import Ranges, ranges_to_list
from encord.objects.ontology_element import _get_element_by_hash
from encord.objects.options import FlatOption, NestableOption
from encord.objects.utils import _lower_snake_case, short_uuid_str

ValueType = TypeVar("ValueType")
AttributeType = TypeVar("AttributeType", bound=Attribute)


class Answer(ABC, Generic[ValueType, AttributeType]):
    """An internal helper class for the LabelRowV2 class. This class is not meant to be used directly by users."""

    _ontology_attribute: AttributeType
    _value: Optional[ValueType]

    def __init__(self, ontology_attribute: AttributeType, track_hash: Optional[str] = None):
        self._answered = False
        self._ontology_attribute = ontology_attribute
        self._track_hash = track_hash or short_uuid_str()
        self._is_manual_annotation = DEFAULT_MANUAL_ANNOTATION
        self._should_propagate = False

    def is_answered(self) -> bool:
        return self._answered

    def unset(self) -> None:
        """Remove the value from the answer"""
        self._answered = False
        self._value = None

    @property
    def is_dynamic(self) -> bool:
        return self._ontology_attribute.dynamic

    @is_dynamic.setter
    def is_dynamic(self, value: bool) -> NoReturn:
        raise RuntimeError("Cannot set the is_dynamic value of the answer.")

    @property
    def is_manual_annotation(self) -> bool:
        return self._is_manual_annotation

    @is_manual_annotation.setter
    def is_manual_annotation(self, value: bool) -> None:
        self._is_manual_annotation = value

    @property
    def ontology_attribute(self) -> AttributeType:
        return self._ontology_attribute

    @ontology_attribute.setter
    def ontology_attribute(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot reset the ontology attribute of an instantiated answer.")

    @abstractmethod
    def set(self, value: ValueType, manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION) -> None:
        pass

    def get(self) -> ValueType:
        if not self.is_answered():
            raise ValueError("Can't read a value of unanswered Answer object")

        assert self._value is not None, "Value can't be none for the answered Answer object"
        return self._value

    def to_encord_dict(self, ranges: Optional[Ranges] = None) -> Optional[Dict[str, Any]]:
        """
        A low level helper to convert to the Encord JSON format.
        For most use cases the `get_answer` function should be used instead.
        """
        if not self.is_answered():
            return None

        ret = self._to_encord_dict_impl(self.is_dynamic)
        if self.is_dynamic:
            if ranges is None:
                raise ValueError("Frame range should be set for dynamic answers")

            ret.update(self._get_encord_dynamic_fields(ranges))

        return ret

    @abstractmethod
    def _to_encord_dict_impl(self, is_dynamic: bool = False) -> Dict[str, Any]:
        pass

    @abstractmethod
    def from_dict(self, d: Dict[str, Any]) -> None:
        pass

    def _get_encord_dynamic_fields(self, ranges: Ranges) -> Dict[str, Any]:
        return {
            "dynamic": True,
            "range": ranges_to_list(ranges),
            "shouldPropagate": self._should_propagate,
            "trackHash": self._track_hash,
        }


class TextAnswer(Answer[str, TextAttribute]):
    def __init__(self, ontology_attribute: TextAttribute):
        super().__init__(ontology_attribute)
        self._value: Optional[str] = None

    def set(self, value: str, manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION) -> None:
        """Returns the object itself"""
        if not isinstance(value, str):
            raise ValueError("TextAnswer can only be set to a string.")
        self._value = value
        self._answered = True
        self.is_manual_annotation = manual_annotation

    def get_value(self) -> Optional[str]:
        return self._value if self.is_answered() else None

    def copy_from(self, text_answer: TextAnswer):
        if text_answer.ontology_attribute.feature_node_hash != self.ontology_attribute.feature_node_hash:
            raise ValueError(
                "Copying from a TextAnswer which is based on a different ontology Attribute is not possible."
            )
        other_is_answered = text_answer.is_answered()
        if not other_is_answered:
            self.unset()
        else:
            other_answer = text_answer.get()
            self.set(other_answer)

    def _to_encord_dict_impl(self, is_dynamic: bool = False) -> Dict[str, Any]:
        return {
            "name": self.ontology_attribute.name,
            "value": _lower_snake_case(self.ontology_attribute.name),
            "answers": self._value,
            "featureHash": self.ontology_attribute.feature_node_hash,
            "manualAnnotation": self.is_manual_annotation,
        }

    def from_dict(self, d: Dict[str, Any]) -> None:
        if d["featureHash"] != self.ontology_attribute.feature_node_hash:
            raise ValueError("Cannot set the value of a TextAnswer based on a different ontology attribute.")

        self.set(d["answers"])
        self.is_manual_annotation = d["manualAnnotation"]

    def __hash__(self):
        return hash((self._ontology_attribute.feature_node_hash, self._value, type(self).__name__))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TextAnswer):
            return False

        return (
            self._ontology_attribute.feature_node_hash == other._ontology_attribute.feature_node_hash
            and self._value == other._value
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self._value})"


@dataclass
class RadioAnswer(Answer[NestableOption, RadioAttribute]):
    def __init__(self, ontology_attribute: RadioAttribute):
        super().__init__(ontology_attribute)
        self._value: Optional[NestableOption] = None

    def set(self, value: NestableOption, manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION) -> None:
        if not isinstance(value, NestableOption):
            raise ValueError("RadioAnswer can only be set to a NestableOption.")

        passed = any(value.feature_node_hash == child.feature_node_hash for child in self._ontology_attribute.options)
        if not passed:
            raise ValueError(
                f"The supplied NestableOption `{value}` is not a child of the RadioAttribute that "
                f"is associated with this class: `{self._ontology_attribute}`"
            )
        self._answered = True
        self._value = value
        self.is_manual_annotation = manual_annotation

    def get_value(self) -> Optional[NestableOption]:
        return self._value if self.is_answered() else None

    def copy_from(self, radio_answer: RadioAnswer):
        if radio_answer.ontology_attribute.feature_node_hash != self.ontology_attribute.feature_node_hash:
            raise ValueError(
                "Copying from a RadioAnswer which is based on a different ontology Attribute is not possible."
            )
        other_is_answered = radio_answer.is_answered()
        if not other_is_answered:
            self.unset()
        else:
            other_answer = radio_answer.get()
            self.set(other_answer)

    def _to_encord_dict_impl(self, is_dynamic: bool = False) -> Dict[str, Any]:
        nestable_option = self._value
        assert nestable_option is not None  # Check is performed earlier, so just to silence mypy

        return {
            "name": self.ontology_attribute.name,
            "value": _lower_snake_case(self.ontology_attribute.name),
            "answers": [
                {
                    "name": nestable_option.label,
                    "value": nestable_option.value,
                    "featureHash": nestable_option.feature_node_hash,
                }
            ],
            "featureHash": self.ontology_attribute.feature_node_hash,
            "manualAnnotation": self.is_manual_annotation,
        }

    def from_dict(self, d: Dict) -> None:
        if d["featureHash"] != self.ontology_attribute.feature_node_hash:
            raise ValueError("Cannot set the value of a TextAnswer based on a different ontology attribute.")

        answers = d["answers"]
        if len(answers) != 1:
            raise ValueError("RadioAnswers must have exactly one answer.")

        answer = answers[0]
        nestable_option = _get_element_by_hash(
            answer["featureHash"], self.ontology_attribute.options, type_=NestableOption
        )
        if nestable_option is None:
            raise ValueError(f"Item not found: can't find an option with a feature hash {answer['featureHash']}")

        self.set(nestable_option)
        self.is_manual_annotation = d["manualAnnotation"]

    def __hash__(self):
        return hash((self.ontology_attribute.feature_node_hash, self._value, type(self).__name__))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RadioAnswer):
            return False

        return (
            self._ontology_attribute.feature_node_hash == other._ontology_attribute.feature_node_hash
            and self._value == other._value
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self._value})"


@dataclass
class ChecklistAnswer(Answer[List[FlatOption], ChecklistAttribute]):
    """
    Checkboxes behave slightly different from the other answer types. When the checkbox is unanswered, it will be
    the equivalent of not having selected any checkbox answer in the Encord platform.
    The initial state will be every checkbox unchecked.
    """

    def __init__(self, ontology_attribute: ChecklistAttribute):
        super().__init__(ontology_attribute)
        self._ontology_options_feature_hashes: Set[str] = self._initialise_ontology_options_feature_hashes()
        self._feature_hash_to_answer_map: Dict[str, bool] = self._initialise_feature_hash_to_answer_map()

    def check_options(self, values: Iterable[FlatOption]):
        self._answered = True
        for value in values:
            self._verify_flat_option(value)
            self._feature_hash_to_answer_map[value.feature_node_hash] = True

    def uncheck_options(self, values: Iterable[FlatOption]):
        self._answered = True
        for value in values:
            self._verify_flat_option(value)
            self._feature_hash_to_answer_map[value.feature_node_hash] = False

    def get(self) -> List[FlatOption]:
        if not self.is_answered():
            raise ValueError("Can't read a value of unanswered Answer object")

        return [
            option
            for option in self._ontology_attribute.options
            if self._feature_hash_to_answer_map[option.feature_node_hash]
        ]

    def set(self, value: Iterable[FlatOption], manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION):
        if not isinstance(value, Iterable):
            raise ValueError(
                "Checklist attribute answer should be an iterable of FlatOption values. "
                "For setting a single option, consider wrapping it in a list: [value]."
            )

        for value_ in value:
            if not isinstance(value_, FlatOption):
                raise ValueError("Checklist attribute values can only be set to FlatOption.")

        self._answered = True
        for key in self._feature_hash_to_answer_map.keys():
            self._feature_hash_to_answer_map[key] = False
        for value_ in value:
            self._verify_flat_option(value_)
            self._feature_hash_to_answer_map[value_.feature_node_hash] = True

        self.is_manual_annotation = manual_annotation

    @deprecated("0.1.91", alternative=".set(options)")
    def set_options(self, values: Iterable[FlatOption]):
        # Deprecated: please use :meth:`set` instead
        return self.set(values)

    @deprecated("0.1.91", alternative=".get()")
    def get_options(self) -> List[FlatOption]:
        # Deprecated: please use :meth:`get()` instead

        if not self.is_answered():
            return []
        else:
            return [
                option
                for option in self._ontology_attribute.options
                if self._feature_hash_to_answer_map[option.feature_node_hash]
            ]

    @deprecated("0.1.91", alternative=".get_option_value(option)")
    def get_value(self, value: FlatOption) -> bool:
        # Deprecated: please use :meth:`get_option_value` instead
        return self.get_option_value(value)

    def get_option_value(self, value: FlatOption) -> bool:
        return self._feature_hash_to_answer_map[value.feature_node_hash]

    def copy_from(self, checklist_answer: ChecklistAnswer):
        if checklist_answer.ontology_attribute.feature_node_hash != self.ontology_attribute.feature_node_hash:
            raise ValueError(
                "Copying from a ChecklistAnswer which is based on a different ontology Attribute is not possible."
            )
        other_is_answered = checklist_answer.is_answered()
        if not other_is_answered:
            self.unset()
        else:
            self._answered = True
            for feature_node_hash in self._feature_hash_to_answer_map.keys():
                option = _get_element_by_hash(feature_node_hash, self.ontology_attribute.options, type_=FlatOption)
                if option is None:
                    raise RuntimeError(f"Item not found: can't find an option with a feature hash {feature_node_hash}")
                other_answer = checklist_answer.get_option_value(option)
                self._feature_hash_to_answer_map[feature_node_hash] = other_answer

    def _initialise_feature_hash_to_answer_map(self) -> Dict[str, bool]:
        return {child.feature_node_hash: False for child in self._ontology_attribute.options}

    def _initialise_ontology_options_feature_hashes(self) -> Set[str]:
        return {child.feature_node_hash for child in self._ontology_attribute.options}

    def _verify_flat_option(self, value: FlatOption) -> None:
        if value.feature_node_hash not in self._ontology_options_feature_hashes:
            raise RuntimeError(
                f"The supplied FlatOption `{value}` is not a child of the ChecklistAttribute that "
                f"is associated with this class: `{self._ontology_attribute}`"
            )

    def _to_encord_dict_impl(self, is_dynamic: bool = False) -> Dict[str, Any]:
        ontology_attribute: ChecklistAttribute = self._ontology_attribute
        checked_options = [option for option in ontology_attribute.options if self.get_option_value(option)]
        answers = [
            {
                "name": option.label,
                "value": option.value,
                "featureHash": option.feature_node_hash,
            }
            for option in checked_options
        ]
        return {
            "name": self.ontology_attribute.name,
            "value": _lower_snake_case(self.ontology_attribute.name),
            "answers": answers,
            "featureHash": self.ontology_attribute.feature_node_hash,
            "manualAnnotation": self.is_manual_annotation,
        }

    def from_dict(self, d: Dict[str, Any]) -> None:
        if d["featureHash"] != self.ontology_attribute.feature_node_hash:
            raise ValueError("Cannot set the value of a ChecklistAnswer based on a different ontology attribute.")

        answers = d["answers"]
        if len(answers) == 0:
            return

        for answer in answers:
            flat_option = _get_element_by_hash(answer["featureHash"], self.ontology_attribute.options, type_=FlatOption)
            if flat_option is None:
                raise ValueError(f"Item not found: can't find an option with a feature hash {answer['featureHash']}")

            self.check_options([flat_option])

        self.is_manual_annotation = d["manualAnnotation"]
        self._answered = True

    def __hash__(self):
        flat_values = sorted(self._feature_hash_to_answer_map.items())
        return hash((tuple(flat_values), type(self).__name__))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChecklistAnswer):
            return False

        flat_values = set(self._feature_hash_to_answer_map.items())
        other_flat_values = set(other._feature_hash_to_answer_map.items())
        return flat_values == other_flat_values

    def __repr__(self):
        flat_values = list(self._feature_hash_to_answer_map.items())
        return f"{self.__class__.__name__}({flat_values})"


def get_default_answer_from_attribute(attribute: Attribute) -> Answer:
    if isinstance(attribute, TextAttribute):
        return TextAnswer(attribute)
    elif isinstance(attribute, RadioAttribute):
        return RadioAnswer(attribute)
    elif isinstance(attribute, ChecklistAttribute):
        return ChecklistAnswer(attribute)
    else:
        raise RuntimeError(f"Got an attribute with an unexpected property type: {attribute}")


def _get_default_static_answers_from_attributes(attributes: List[Attribute]) -> List[Answer]:
    ret: List[Answer] = []
    for attribute in attributes:
        if not attribute.dynamic:
            answer = get_default_answer_from_attribute(attribute)
            ret.append(answer)

        for option in attribute.options:
            other_attributes = _get_default_static_answers_from_attributes(option.attributes)
            ret.extend(other_attributes)

    return ret


def _get_static_answer_map(attributes: List[Attribute]) -> Dict[str, Answer]:
    answers = _get_default_static_answers_from_attributes(attributes)
    return {answer.ontology_attribute.feature_node_hash: answer for answer in answers}
