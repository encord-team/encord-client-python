from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Union

from encord.exceptions import LabelRowError
from encord.objects.answers import Answer
from encord.objects.attributes import Attribute, RadioAttribute, TextAttribute
from encord.objects.options import Option


def _search_child_attributes(
    passed_attribute: Attribute, search_attribute: Attribute, static_answer_map: Dict[str, Answer]
) -> bool:
    if passed_attribute == search_attribute:
        return True

    if not isinstance(search_attribute, RadioAttribute):
        return False

    answer = static_answer_map[search_attribute.feature_node_hash]
    if not answer.is_answered():
        return False

    value = answer.get()
    for option in search_attribute.options:
        if value == option:
            for nested_option in option.nested_options:
                # If I have multi nesting here, what then?
                if _search_child_attributes(passed_attribute, nested_option, static_answer_map):
                    return True

    return False


def _search_for_parent(passed_option: Option, attributes: List[Attribute]) -> Optional[Attribute]:
    for attribute in attributes:
        for option in attribute.options:
            if option == passed_option:
                return attribute

            attribute_opt = _search_for_parent(passed_option, option.attributes)
            if attribute_opt is not None:
                return attribute_opt
    return None


def _search_for_text_attributes(attributes: List[Attribute]) -> List[TextAttribute]:
    text_attributes: List[TextAttribute] = []
    for attribute in attributes:
        if isinstance(attribute, TextAttribute):
            text_attributes.append(attribute)

        for option in attribute.options:
            text_attributes.extend(_search_for_text_attributes(option.attributes))
    return text_attributes


def _infer_attribute_from_answer(
    attributes: List[Attribute], answer: Union[str, Option, Sequence[Option]]
) -> Attribute:
    if isinstance(answer, Option):
        parent_opt = _search_for_parent(answer, attributes)  # type: ignore
        if parent_opt is None:
            raise LabelRowError(
                "Cannot find a corresponding attribute for the given answer in the Object ontology. "
                "Please ensure to only pass the correct answer options for the given Object ontology. "
                f"The used answer is `{answer}`"
            )
        return parent_opt

    elif isinstance(answer, str):
        text_attributes = _search_for_text_attributes(attributes)
        if len(text_attributes) == 0:
            raise LabelRowError(
                "Cannot find any text attribute in the ontology of the given instance. Setting "
                "a text answer is not supported."
            )
        if len(text_attributes) > 1:
            raise LabelRowError(
                "Multiple text attributes are present in the ontology of the given instance. "
                f"Please provide the attribute explicitly. The found text attributes are {text_attributes}"
            )
        return text_attributes[0]

    elif isinstance(answer, Sequence):
        if len(answer) == 0:
            raise LabelRowError(
                "Cannot infer the attribute if a list of answers is empty. Please provide the attribute explicitly."
            )

        assert isinstance(answer[0], Option)  # Narrowing type here as sequence can contain only Options
        parent_opt = _search_for_parent(answer[0], attributes)
        if parent_opt is None:
            raise LabelRowError(
                "Cannot find a corresponding attribute for one of the given answers in the Object ontology. "
                "Please ensure to only pass the correct answer options for the given Object ontology. "
                f"The used answer is `{answer}`"
            )
        for option in answer:
            if option not in parent_opt.options:
                raise LabelRowError(
                    "Multiple options have been provided that do not belong to the same attribute. Please ensure that "
                    "all options belong to the same ontology attribute."
                )
        return parent_opt

    else:
        raise NotImplementedError(f"The answer type is not supported for answer `{answer}` of type {type(answer)}.")
