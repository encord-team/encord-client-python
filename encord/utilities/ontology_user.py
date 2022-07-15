from dataclasses import dataclass
from enum import IntEnum


class OntologyUserRole(IntEnum):
    ADMIN = 0
    USER = 1


@dataclass(frozen=True)
class OntologyWithUserRole:
    """
    This is a helper class denoting the relationship between the current user an an ontology
    """

    user_role: int
    user_email: str
    ontology: dict
