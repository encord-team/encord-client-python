from dataclasses import dataclass
from typing import List

from cord.project_ontology.classification_attribute import ClassificationAttribute


@dataclass
class OntologyClassification:
    id: str
    feature_node_hash: str
    attributes: List[ClassificationAttribute]

