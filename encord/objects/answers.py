"""
---
title: "Objects - Answers"
slug: "sdk-ref-objects-answer"
hidden: false
metadata:
  title: "Objects - Answers"
  description: "Encord SDK Objects - Answers class."
category: "64e481b57b6027003f20aaa0"
---
"""

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
        """Initialize the Answer instance with the given ontology attribute and track hash."""
        self._answered = False
        self._ontology_attribute = ontology_attribute
        self._track_hash = track_hash or short_uuid_str()
        self._is_manual_annotation = DEFAULT_MANUAL_ANNOTATION
        self._should_propagate = False

    def is_answered(self) -> bool:
        """Check if the answer has been provided."""
        return self._answered

    def unset(self) -> None:
        """Remove the value from the answer."""
        self._answered = False
        self._value = None

    @property
    def is_dynamic(self) -> bool:
        """Check if the attribute is dynamic."""
        return self._ontology_attribute.dynamic

    @is_dynamic.setter
    def is_dynamic(self, value: bool) -> NoReturn:
        raise RuntimeError("Cannot set the is_dynamic value of the answer.")

    @property
    def is_manual_annotation(self) -> bool:
        """Get the manual annotation status."""
        return self._is_manual_annotation

    @is_manual_annotation.setter
    def is_manual_annotation(self, value: bool) -> None:
        """Set the manual annotation status."""
        self._is_manual_annotation = value

    @property
    def ontology_attribute(self) -> AttributeType:
        """Get the ontology attribute."""
        return self._ontology_attribute

    @ontology_attribute.setter
    def ontology_attribute(self, v: Any) -> NoReturn:
        raise RuntimeError("Cannot reset the ontology attribute of an instantiated answer.")

    @abstractmethod
    def set(self, value: ValueType, manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION) -> None:
        """Set the value of the answer."""
        pass

    def get(self) -> ValueType:
        """Get the value of the answer."""
        if not self.is_answered():
            raise ValueError("Can't read a value of unanswered Answer object")

        assert self._value is not None, "Value can't be none for the answered Answer object"
        return self._value

    def to_encord_dict(self, ranges: Optional[Ranges] = None) -> Optional[Dict[str, Any]]:
        """
        Convert to the Encord JSON format.
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
        """Helper function to convert to Encord JSON format."""
        pass

    @abstractmethod
    def from_dict(self, d: Dict[str, Any]) -> None:
        """Populate the answer from a dictionary."""
        pass

    def _get_encord_dynamic_fields(self, ranges: Ranges) -> Dict[str, Any]:
        """Get the dynamic fields for the Encord JSON format."""
        return {
            "dynamic": True,
            "range": ranges_to_list(ranges),
            "shouldPropagate": self._should_propagate,
            "trackHash": self._track_hash,
        }


class TextAnswer(Answer[str, TextAttribute]):
    """Class representing an answer for a text attribute."""

    def __init__(self, ontology_attribute: TextAttribute):
        """Initialize the TextAnswer instance with the given ontology attribute."""
        super().__init__(ontology_attribute)
        self._value: Optional[str] = None

    def set(self, value: str, manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION) -> None:
        """Set the value of the text answer."""
        if not isinstance(value, str):
            raise ValueError("TextAnswer can only be set to a string.")
        self._value = value
        self._answered = True
        self.is_manual_annotation = manual_annotation

    def get_value(self) -> Optional[str]:
        """Get the value of the text answer if it is answered."""
        return self._value if self.is_answered() else None

    def copy_from(self, text_answer: TextAnswer):
        """Copy the value from another TextAnswer instance."""
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
        """Convert to the Encord JSON format."""
        return {
            "name": self.ontology_attribute.name,
            "value": _lower_snake_case(self.ontology_attribute.name),
            "answers": self._value,
            "featureHash": self.ontology_attribute.feature_node_hash,
            "manualAnnotation": self.is_manual_annotation,
        }

    def from_dict(self, d: Dict[str, Any]) -> None:
        """Populate the TextAnswer from a dictionary."""
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
    """Class representing an answer for a radio attribute."""

    def __init__(self, ontology_attribute: RadioAttribute):
        """Initialize the RadioAnswer instance with the given ontology attribute."""
        super().__init__(ontology_attribute)
        self._value: Optional[NestableOption] = None

    def set(self, value: NestableOption, manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION) -> None:
        """Set the value of the radio answer."""
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
        """Get the value of the radio answer if it is answered."""
        return self._value if self.is_answered() else None

    def copy_from(self, radio_answer: RadioAnswer):
        """Copy the value from another RadioAnswer instance."""
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
        """Convert to the Encord JSON format."""
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

    def from_dict(self, d: Dict[str, Any]) -> None:
        """Populate the RadioAnswer from a dictionary."""
        if d["featureHash"] != self.ontology_attribute.feature_node_hash:
            raise ValueError("Cannot set the value of a RadioAnswer based on a different ontology attribute.")

        answers = d["answers"]
        if len(answers) != 1:
            raise ValueError("RadioAnswer must have exactly one answer.")

        nestable_option = _get_element_by_hash(self.ontology_attribute.options, answers[0]["featureHash"])
        self.set(nestable_option)
        self.is_manual_annotation = d["manualAnnotation"]

    def __hash__(self):
        return hash((self._ontology_attribute.feature_node_hash, self._value, type(self).__name__))

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
class ChecklistAnswer(Answer[Set[FlatOption], ChecklistAttribute]):
    """Class representing an answer for a checklist attribute."""

    def __init__(self, ontology_attribute: ChecklistAttribute):
        """Initialize the ChecklistAnswer instance with the given ontology attribute."""
        super().__init__(ontology_attribute)
        self._value: Set[FlatOption] = set()

    def set(
        self,
        value: Iterable[FlatOption] | FlatOption,
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
    ) -> None:
        """Set the value(s) of the checklist answer."""
        if isinstance(value, FlatOption):
            value = {value}

        value = set(value)
        if not all(isinstance(option, FlatOption) for option in value):
            raise ValueError("ChecklistAnswer can only be set to a FlatOption or an iterable of FlatOption.")

        value_set = set(value)
        passed = all(
            any(option.feature_node_hash == child.feature_node_hash for child in self._ontology_attribute.options)
            for option in value_set
        )
        if not passed:
            raise ValueError(
                f"The supplied FlatOption `{value}` is not a child of the ChecklistAttribute that "
                f"is associated with this class: `{self._ontology_attribute}`"
            )

        self._answered = True
        self._value = value_set
        self.is_manual_annotation = manual_annotation

    def get_value(self) -> Set[FlatOption]:
        """Get the value(s) of the checklist answer."""
        return self._value if self.is_answered() else set()

    def add(self, value: FlatOption) -> None:
        """Add a single FlatOption to the checklist answer."""
        if not isinstance(value, FlatOption):
            raise ValueError("ChecklistAnswer can only be set to a FlatOption.")

        passed = any(value.feature_node_hash == child.feature_node_hash for child in self._ontology_attribute.options)
        if not passed:
            raise ValueError(
                f"The supplied FlatOption `{value}` is not a child of the ChecklistAttribute that "
                f"is associated with this class: `{self._ontology_attribute}`"
            )

        self._answered = True
        self._value.add(value)

    def remove(self, value: FlatOption) -> None:
        """Remove a single FlatOption from the checklist answer."""
        if not isinstance(value, FlatOption):
            raise ValueError("ChecklistAnswer can only be set to a FlatOption.")

        passed = any(value.feature_node_hash == child.feature_node_hash for child in self._ontology_attribute.options)
        if not passed:
            raise ValueError(
                f"The supplied FlatOption `{value}` is not a child of the ChecklistAttribute that "
                f"is associated with this class: `{self._ontology_attribute}`"
            )

        self._value.discard(value)
        self._answered = bool(self._value)

    def toggle(self, value: FlatOption) -> None:
        """Toggle the presence of a FlatOption in the checklist answer."""
        if not isinstance(value, FlatOption):
            raise ValueError("ChecklistAnswer can only be set to a FlatOption.")

        passed = any(value.feature_node_hash == child.feature_node_hash for child in self._ontology_attribute.options)
        if not passed:
            raise ValueError(
                f"The supplied FlatOption `{value}` is not a child of the ChecklistAttribute that "
                f"is associated with this class: `{self._ontology_attribute}`"
            )

        if value in self._value:
            self._value.remove(value)
        else:
            self._value.add(value)
        self._answered = bool(self._value)

    def copy_from(self, checklist_answer: ChecklistAnswer):
        """Copy the value(s) from another ChecklistAnswer instance."""
        if checklist_answer.ontology_attribute.feature_node_hash != self.ontology_attribute.feature_node_hash:
            raise ValueError(
                "Copying from a ChecklistAnswer which is based on a different ontology Attribute is not possible."
            )
        other_is_answered = checklist_answer.is_answered()
        if not other_is_answered:
            self.unset()
        else:
            other_answer = checklist_answer.get()
            self.set(other_answer)

    def _to_encord_dict_impl(self, is_dynamic: bool = False) -> Dict[str, Any]:
        """Convert to the Encord JSON format."""
        checklist = [{"name": option.label, "value": option.value, "featureHash": option.feature_node_hash}
                     for option in self._value]

        return {
            "name": self.ontology_attribute.name,
            "value": _lower_snake_case(self.ontology_attribute.name),
            "answers": checklist,
            "featureHash": self.ontology_attribute.feature_node_hash,
            "manualAnnotation": self.is_manual_annotation,
        }

    def from_dict(self, d: Dict[str, Any]) -> None:
        """Populate the ChecklistAnswer from a dictionary."""
        if d["featureHash"] != self.ontology_attribute.feature_node_hash:
            raise ValueError("Cannot set the value of a ChecklistAnswer based on a different ontology attribute.")

        answers = d["answers"]
        new_values = set()
        for answer in answers:
            flat_option = _get_element_by_hash(self.ontology_attribute.options, answer["featureHash"])
            new_values.add(flat_option)

        self.set(new_values)
        self.is_manual_annotation = d["manualAnnotation"]

    def __hash__(self):
        return hash((self._ontology_attribute.feature_node_hash, frozenset(self._value), type(self).__name__))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChecklistAnswer):
            return False

        return (
            self._ontology_attribute.feature_node_hash == other._ontology_attribute.feature_node_hash
            and self._value == other._value
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self._value})"