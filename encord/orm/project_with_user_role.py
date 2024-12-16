from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectWithUserRole:
    """
    This is a helper class denoting the relationship between the current user an a project
    """

    user_role: int
    project: dict
