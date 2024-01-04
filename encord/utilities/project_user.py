from enum import IntEnum

from encord.orm.base_dto import BaseDTO


class ProjectUserRole(IntEnum):
    ADMIN = (0,)
    ANNOTATOR = (1,)
    REVIEWER = (2,)
    ANNOTATOR_REVIEWER = (3,)
    TEAM_MANAGER = 4


class ProjectUser(BaseDTO):
    user_email: str
    user_role: ProjectUserRole
    project_hash: str
