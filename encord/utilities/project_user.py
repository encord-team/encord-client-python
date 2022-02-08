from dataclasses import dataclass
from enum import IntEnum
from typing import Dict

from encord.orm.formatter import Formatter


class ProjectUserRole(IntEnum):
    ADMIN = (0,)
    ANNOTATOR = (1,)
    REVIEWER = (2,)
    ANNOTATOR_REVIEWER = (3,)
    TEAM_MANAGER = 4


@dataclass(frozen=True)
class ProjectUser(Formatter):
    user_email: str
    user_role: ProjectUserRole
    project_hash: str

    @classmethod
    def from_dict(cls, json_dict: Dict):
        return ProjectUser(json_dict["user_email"], ProjectUserRole(json_dict["user_role"]), json_dict["project_hash"])
