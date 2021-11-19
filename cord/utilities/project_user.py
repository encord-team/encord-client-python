from dataclasses import dataclass
from enum import IntEnum


class ProjectUserRole(IntEnum):
    ADMIN = 0,
    ANNOTATOR = 1,
    REVIEWER = 2,
    ANNOTATOR_REVIEWER = 3,
    TEAM_MANAGER = 4


@dataclass(frozen=True)
class ProjectUser:
    user_id: int
    user_hash: str
    user_email: str
    user_role: ProjectUserRole
    project_hash: str
