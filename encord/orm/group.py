from datetime import datetime
from uuid import UUID

from encord.orm.base_dto import BaseDTO
from encord.orm.dataset import DatasetUserRole
from encord.utilities.ontology_user import OntologyUserRole
from encord.utilities.project_user import ProjectUserRole


class Group(BaseDTO):
    group_hash: str
    name: str
    description: str
    created_at: datetime


class ProjectGroup(Group):
    user_role: ProjectUserRole
    is_same_organisation: bool


class OntologyGroup(Group):
    user_role: OntologyUserRole
    is_same_organisation: bool


class DatasetGroup(Group):
    user_role: DatasetUserRole
    is_same_organisation: bool


class ProjectGroupParam(BaseDTO):
    group_hash: str
    user_role: ProjectUserRole


class DatasetGroupParam(BaseDTO):
    group_hash: str
    user_role: DatasetUserRole


class OntologyGroupParam(BaseDTO):
    group_hash: str
    user_role: OntologyUserRole
