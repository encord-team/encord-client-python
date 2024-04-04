from datetime import datetime
from typing import List
from uuid import UUID

from encord.orm.base_dto import BaseDTO
from encord.orm.dataset import DatasetUserRole
from encord.utilities.ontology_user import OntologyUserRole
from encord.utilities.project_user import ProjectUserRole


class Group(BaseDTO):
    group_hash: UUID
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


class AddGroupsPayload(BaseDTO):
    group_hash_list: List[UUID]


class AddProjectGroupsPayload(AddGroupsPayload):
    user_role: ProjectUserRole


class AddDatasetGroupsPayload(AddGroupsPayload):
    user_role: DatasetUserRole


class AddOntologyGroupsPayload(AddGroupsPayload):
    user_role: OntologyUserRole


class RemoveGroupsParams(BaseDTO):
    group_hash_list: List[UUID]
