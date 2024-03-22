from datetime import datetime
from uuid import UUID
from encord.orm.base_dto import BaseDTO


class Group(BaseDTO):
    group_hash: UUID
    name: str
    description: str
    created_at: datetime
