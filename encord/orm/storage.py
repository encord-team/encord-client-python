from datetime import datetime
from enum import auto
from typing import Any, Dict, Optional
from uuid import UUID

from encord.orm.analytics import CamelStrEnum
from encord.orm.base_dto import BaseDTO


class StorageUserRole(CamelStrEnum):
    USER = auto()
    ADMIN = auto()


class StorageFolder(BaseDTO):
    uuid: UUID
    parent: Optional[UUID]
    name: str
    description: str
    client_metadata: Optional[str]
    owner: str
    created_at: datetime
    last_edited_at: datetime
    user_role: StorageUserRole
    synced_dataset_hash: Optional[UUID]


class CreateStorageFolderPayload(BaseDTO):
    name: str
    description: Optional[str]
    parent: Optional[UUID]
    client_metadata: Optional[str]
