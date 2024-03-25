from datetime import datetime
from uuid import UUID
from encord.orm.base_dto import BaseDTO
from encord.orm.dataset import DatasetUserRole
from encord.utilities.project_user import ProjectUserRole


class Group(BaseDTO):
    group_hash: UUID
    name: str
    description: str
    created_at: datetime


class ProjectGroupParam(BaseDTO):
    group_hash: UUID
    user_role: ProjectUserRole


class DatasetGroupParam(BaseDTO):
    group_hash: UUID
    user_role: DatasetUserRole

class OntologyGroupParam(BaseDTO):
    group_hash: UUID
    user_role: DatasetUserRole
