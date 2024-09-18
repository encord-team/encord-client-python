from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetWithUserRole:
    """
    This is a helper class denoting the relationship between the current user and a project
    """

    user_role: int
    dataset: dict
