from dataclasses import dataclass

from encord.utilities.project_user import ProjectUserRole


@dataclass
class CollaboratorTimer:
    user_email: str
    user_role: ProjectUserRole
    data_title: str
    time_seconds: float
