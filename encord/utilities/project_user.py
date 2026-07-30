from enum import IntEnum
from typing import Any

from encord.orm.base_dto import BaseDTO


class ProjectUserRole(IntEnum):
    """Enumeration for user roles within a project.

    Attributes:
        ADMIN (int): Represents an admin user with value 0.
        ANNOTATOR (int): Represents an annotator user with value 1.
        REVIEWER (int): Represents a reviewer user with value 2.
        ANNOTATOR_REVIEWER (int): Represents a user who is both an annotator and a reviewer with value 3.
        TEAM_MANAGER (int): Represents a team manager user with value 4.
        VIEWER (int): Represents a read-only viewer user with value 5.
        UNKNOWN (int): Represents an unsupported role returned by a newer API version.
    """

    ADMIN = (0,)
    ANNOTATOR = (1,)
    REVIEWER = (2,)
    ANNOTATOR_REVIEWER = (3,)
    TEAM_MANAGER = 4
    VIEWER = 5
    UNKNOWN = -99

    @classmethod
    def _missing_(cls, value: Any) -> "ProjectUserRole":
        return cls.UNKNOWN


class ProjectUser(BaseDTO):
    """Data transfer object representing a user within a project.

    Attributes:
        user_email (str): The email address of the user.
        user_role (ProjectUserRole): The role of the user in the project, defined by the ProjectUserRole enumeration.
        project_hash (str): A unique identifier for the project.
    """

    user_email: str
    user_role: ProjectUserRole
    project_hash: str
