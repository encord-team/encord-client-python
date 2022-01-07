from dataclasses import dataclass


@dataclass
class ClassificationOption:
    id: str
    label: str
    value: str
    feature_node_hash: str
