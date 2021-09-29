from __future__ import annotations

from cord.configs import UserConfig
from cord.http.querier import Querier
from cord.orm.dataset import Dataset, DatasetType


class CordUserClient:
    def __init__(self, user_config: UserConfig, querier: Querier):
        self.user_config = user_config
        self.querier = querier

    def create_private_dataset(self, dataset_title: str, dataset_type: DatasetType, dataset_description: str = None):
        dataset = {
            'title': dataset_title,
            'type': dataset_type,
        }

        if dataset_description:
            dataset['description'] = dataset_description

        return self.querier.basic_setter(Dataset, uid=None, payload=dataset)

    @staticmethod
    def create_with_ssh_private_key(ssh_private_key: str, password: str = None, **kwargs) -> CordUserClient:
        user_config = UserConfig.from_ssh_private_key(ssh_private_key, password, **kwargs)
        querier = Querier(user_config)

        return CordUserClient(user_config, querier)
