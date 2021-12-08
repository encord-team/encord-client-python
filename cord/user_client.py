from __future__ import annotations

from typing import List

from cord.configs import UserConfig
from cord.http.querier import Querier
from cord.orm.cloud_integration import CloudIntegration
from cord.orm.dataset import Dataset, DatasetType
from cord.orm.dataset import DatasetScope, DatasetAPIKey
from cord.orm.project import Project
from cord.orm.project_api_key import ProjectAPIKey
from cord.utilities.client_utilities import APIKeyScopes


class CordUserClient:
    def __init__(self, user_config: UserConfig, querier: Querier):
        self.user_config = user_config
        self.querier = querier

    def create_private_dataset(self, dataset_title: str, dataset_type: DatasetType, dataset_description: str = None):
        return self.create_dataset(dataset_title, dataset_type, dataset_description)

    def create_dataset(self, dataset_title: str, dataset_type: DatasetType, dataset_description: str = None):
        dataset = {
            'title': dataset_title,
            'type': dataset_type,
        }

        if dataset_description:
            dataset['description'] = dataset_description

        return self.querier.basic_setter(Dataset, uid=None, payload=dataset)

    def create_dataset_api_key(
            self, dataset_hash: str, api_key_title: str, dataset_scopes: List[DatasetScope]) -> DatasetAPIKey:
        api_key_payload = {
            'dataset_hash': dataset_hash,
            'title': api_key_title,
            'scopes': list(map(lambda scope: scope.value, dataset_scopes))
        }
        response = self.querier.basic_setter(DatasetAPIKey, uid=None, payload=api_key_payload)
        return DatasetAPIKey.from_dict(response)

    def get_dataset_api_keys(self, dataset_hash: str) -> List[DatasetAPIKey]:
        api_key_payload = {
            'dataset_hash': dataset_hash,
        }
        api_keys: List[DatasetAPIKey] = self.querier.get_multiple(DatasetAPIKey, uid=None, payload=api_key_payload)
        return api_keys

    @staticmethod
    def create_with_ssh_private_key(ssh_private_key: str, password: str = None, **kwargs) -> CordUserClient:
        user_config = UserConfig.from_ssh_private_key(ssh_private_key, password, **kwargs)
        querier = Querier(user_config)

        return CordUserClient(user_config, querier)

    def create_project(self, project_title: str, dataset_hashes: List[str], project_description: str = "") -> str:
        project = {
            'title': project_title,
            'description': project_description,
            'dataset_hashes': dataset_hashes
        }

        return self.querier.basic_setter(Project, uid=None, payload=project)

    def create_project_api_key(self, project_hash: str, api_key_title: str, scopes: List[APIKeyScopes]) -> str:
        payload = {
            'title': api_key_title,
            'scopes': list(map(lambda scope: scope.value, scopes))
        }

        return self.querier.basic_setter(ProjectAPIKey, uid=project_hash, payload=payload)

    def get_project_api_keys(self, project_hash: str) -> List[ProjectAPIKey]:
        return self.querier.get_multiple(ProjectAPIKey, uid=project_hash)

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self.querier.get_multiple(CloudIntegration)

