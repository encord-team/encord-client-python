from dataclasses import dataclass
from typing import Iterable, List, Optional

from encord.project_ontology.classification_option import ClassificationOption
from encord.project_ontology.classification_type import ClassificationType


@dataclass
class ClassificationAttribute:
    id: str
    name: str
    classification_type: ClassificationType
    required: bool
    feature_node_hash: str
    options: Optional[Iterable[ClassificationOption]] = None

    def __setattr__(self, name, value):
        if (name == "classification_type" and value == ClassificationType.TEXT and self.__dict__.get("options")) or (
            name == "options" and value and self.__dict__.get("classification_type") == ClassificationType.TEXT
        ):
            raise Exception("cannot assign options to a classification text")
        self.__dict__[name] = value
