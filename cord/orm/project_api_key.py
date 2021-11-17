from dataclasses import dataclass

from cord.utilities.client_utilities import APIKeyScopes


@dataclass(frozen=True)
class ProjectAPIKey:
    api_Key: str
    title: str
    scopes: APIKeyScopes
