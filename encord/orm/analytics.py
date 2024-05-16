from datetime import datetime
from enum import auto
from typing import Optional

from orm.base_types import CamelStrEnum

from encord.orm.base_dto import BaseDTO
from encord.utilities.project_user import ProjectUserRole


class CollaboratorTimersGroupBy(CamelStrEnum):
    DATA_UNIT = auto()
    PROJECT = auto()


class CollaboratorTimerParams(BaseDTO):
    project_hash: str
    after: datetime
    before: Optional[datetime] = None
    group_by: CollaboratorTimersGroupBy = CollaboratorTimersGroupBy.DATA_UNIT
    page_size: int = 100
    page_token: Optional[str] = None


class CollaboratorTimer(BaseDTO):
    user_email: str
    user_role: ProjectUserRole
    data_title: Optional[str] = None
    time_seconds: float
