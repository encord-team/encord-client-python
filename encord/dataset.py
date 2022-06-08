from typing import List

from encord.client import EncordClientDataset
from encord.configs import Config
from encord.http.querier import Querier
from encord.orm.dataset import DataRow
from encord.orm.dataset import Dataset as OrmDataset
from encord.orm.dataset import StorageLocation


class Dataset(EncordClientDataset):
    def __init__(self, querier: Querier, config: Config):
        super().__init__(querier, config)
        self._dataset_instance = None

    def _get_dataset_instance(self):
        if self._dataset_instance is None:
            self._dataset_instance = self.get_dataset()
        return self._dataset_instance

    @property
    def title(self) -> str:
        """
        Get the title of the dataset
        Returns: title
        """
        dataset_instance = self._get_dataset_instance()
        return dataset_instance.title

    @property
    def description(self) -> str:
        """
        Get the description of the dataset
        """
        dataset_instance = self._get_dataset_instance()
        return dataset_instance.description

    @property
    def storage_location(self) -> StorageLocation:
        """..."""
        dataset_instance = self._get_dataset_instance()
        return dataset_instance.storage_location

    @property
    def data_rows(self) -> List[DataRow]:
        """..."""
        dataset_instance = self._get_dataset_instance()
        return dataset_instance.data_rows

    def refetch_data(self) -> None:
        """
        The Dataset class will only fetch its properties once. Use this function if you suspect the state of those
        properties to be dirty.
        """
        self._dataset_instance = self.get_dataset()

    def get_dataset(self) -> OrmDataset:
        """
        This function is exposed for convenience. You are encouraged to use the property accessors instead.
        """
        return super().get_dataset()
