from dataclasses import dataclass


@dataclass
class ClassificationOption:
    """
    DEPRECATED: prefer using :class:`encord.ontology.Ontology`

    A dataclass which holds nested options for the :class:`.ClassificationAttribute`.
    """

    #: A unique (to the ontology) identifier of the option.
    id: str
    #: A description of the option.
    label: str
    #: A snake-case concatenated version of the label.
    value: str
    #: An 8-character hex string uniquely defining the option.
    feature_node_hash: str
