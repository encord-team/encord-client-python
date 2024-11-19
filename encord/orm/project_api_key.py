import json
from dataclasses import dataclass
from typing import Dict, List

from encord.common.deprecated import deprecated
from encord.orm.formatter import Formatter
from encord.utilities.client_utilities import APIKeyScopes


@dataclass(frozen=True)
class ProjectAPIKey(Formatter):
    """
    DEPRECATED: ProjectAPIKey functionality is being deprecated.
    Use EncordUserClient SSH authentication going forward.

    DEPRECATED -  Obtain project_client:
    project_client = EncordClientProject.initialise(project_hash, project_api_key)

    RECOMMENDED - Obtain project_client:
    project_client = EncordUserClient.create_with_ssh_private_key(ssh_private_key).get_project(project_hash)
    """

    api_key: str
    title: str
    scopes: List[APIKeyScopes]

    @classmethod
    @deprecated("0.1.141", "EncordUserClient.create_with_ssh_private_key(...).get_project(...)")
    def from_dict(cls, json_dict: Dict):
        if isinstance(json_dict["scopes"], str):
            json_dict["scopes"] = json.loads(json_dict["scopes"])
        scopes = [APIKeyScopes(scope) for scope in json_dict["scopes"]]
        return ProjectAPIKey(json_dict["api_key"], json_dict["title"], scopes)
