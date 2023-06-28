from datetime import datetime
from enum import Enum, auto
from typing import Optional

from encord.objects.utils import _snake_to_camel
from encord.orm.base_dto import BaseDTO
from encord.utilities.project_user import ProjectUserRole


class CamelStrEnum(str, Enum):
    # noinspection PyMethodParameters
    def _generate_next_value_(name, start, count, last_values) -> str:  # type: ignore
        return _snake_to_camel(name)


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
