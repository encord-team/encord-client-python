from datetime import datetime
from uuid import UUID
from encord.orm.base_dto import BaseDTO
from encord.utilities.project_user import ProjectUserRole


class Group(BaseDTO):
    group_hash: UUID
    name: str
    description: str
    created_at: datetime


class ProjectGroupParam(BaseDTO):
    group_hash: UUID
    user_role: ProjectUserRole
