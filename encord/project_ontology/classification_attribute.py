from dataclasses import dataclass
from typing import Iterable, Optional

from encord.project_ontology.classification_option import ClassificationOption
from encord.project_ontology.classification_type import ClassificationType


@dataclass
class ClassificationAttribute:
    """
    DEPRECATED: prefer using :class:`encord.ontology.Ontology`

    A dataclass which holds classification attributes.
    """

    #: A unique (to the ontology) identifier of the attribute.
    id: str
    #: The descriptive name of the attribute.
    name: str
    #: What type of attribute it is. E.g., Checkbox or radio button.
    classification_type: ClassificationType
    #: Whether annotating this attribute is required.
    required: bool
    #: An 8-character hex string uniquely defining the attribute.
    feature_node_hash: str
    #: Nested classification options.
    options: Optional[Iterable[ClassificationOption]] = None

    def __setattr__(self, name, value):
        if (name == "classification_type" and value == ClassificationType.TEXT and self.__dict__.get("options")) or (
            name == "options" and value and self.__dict__.get("classification_type") == ClassificationType.TEXT
        ):
            raise Exception("cannot assign options to a classification text")
        self.__dict__[name] = value
