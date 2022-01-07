from dataclasses import dataclass

from cord.project_ontology.object_type import ObjectShape


@dataclass
class OntologyObject:
    id: str
    color: str
    name: str
    shape: ObjectShape
    feature_node_hash: str
