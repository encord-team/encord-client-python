from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from encord.objects.classification import Classification
from encord.objects.ontology_object import Object


@dataclass
class Ontology:
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    objects: List[Object] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> Ontology:
        """
        Args:
            d: a JSON blob of an "editor

        Raises:
            KeyError: If the dict is missing a required field.
        """
        objects_ret: List[Object] = list()
        for object_dict in d["objects"]:
            objects_ret.append(Object.from_dict(object_dict))

        classifications_ret: List[Classification] = list()
        for classification_dict in d["classifications"]:
            classifications_ret.append(Classification.from_dict(classification_dict))

        return Ontology(objects=objects_ret, classifications=classifications_ret)

    def to_dict(self) -> dict:
        """
        Returns:
            The dict equivalent to the ontology.

        Raises:
            KeyError: If the dict is missing a required field.
        """
        ret = dict()
        ontology_objects = list()
        ret["objects"] = ontology_objects
        for ontology_object in self.objects:
            ontology_objects.append(ontology_object.to_dict())

        ontology_classifications = list()
        ret["classifications"] = ontology_classifications
        for ontology_classification in self.classifications:
            ontology_classifications.append(ontology_classification.to_dict())

        return ret
