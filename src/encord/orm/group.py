from datetime import datetime
from typing import List
from uuid import UUID

from encord.orm.base_dto import BaseDTO
from encord.orm.dataset import DatasetUserRole
from encord.orm.storage import StorageUserRole
from encord.utilities.ontology_user import OntologyUserRole
from encord.utilities.project_user import ProjectUserRole


class Group(BaseDTO):
    group_hash: UUID
    name: str
    description: str
    created_at: datetime


class EntityGroup(Group):
    is_same_organisation: bool


class ProjectGroup(EntityGroup):
    user_role: ProjectUserRole


class OntologyGroup(EntityGroup):
    user_role: OntologyUserRole


class DatasetGroup(EntityGroup):
    user_role: DatasetUserRole


class StorageFolderGroup(EntityGroup):
    user_role: StorageUserRole


class AddGroupsPayload(BaseDTO):
    group_hash_list: List[UUID]


class AddProjectGroupsPayload(AddGroupsPayload):
    user_role: ProjectUserRole


class AddDatasetGroupsPayload(AddGroupsPayload):
    user_role: DatasetUserRole


class AddOntologyGroupsPayload(AddGroupsPayload):
    user_role: OntologyUserRole


class AddStorageFolderGroupsPayload(AddGroupsPayload):
    user_role: StorageUserRole


class RemoveGroupsParams(BaseDTO):
    group_hash_list: List[UUID]
