import json
from dataclasses import dataclass
from typing import Dict, List

from encord.orm.formatter import Formatter
from encord.utilities.client_utilities import APIKeyScopes


@dataclass(frozen=True)
class ProjectAPIKey(Formatter):
    api_key: str
    title: str
    scopes: List[APIKeyScopes]

    @classmethod
    def from_dict(cls, json_dict: Dict):
        if isinstance(json_dict["scopes"], str):
            json_dict["scopes"] = json.loads(json_dict["scopes"])
        scopes = [APIKeyScopes(scope) for scope in json_dict["scopes"]]
        return ProjectAPIKey(json_dict["api_key"], json_dict["title"], scopes)
