from dataclasses import dataclass

from encord.utilities.project_user import ProjectUserRole


@dataclass
class CollaboratorSession:
    user_email: str
    user_role: ProjectUserRole
    data_title: str
    session_time_seconds: float
