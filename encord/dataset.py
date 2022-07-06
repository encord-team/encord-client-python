from pathlib import Path
from typing import Dict, Iterable, List, Optional, TextIO, Union

from encord.client import EncordClientDataset
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import AddPrivateDataResponse, DataRow
from encord.orm.dataset import Dataset as OrmDataset
from encord.orm.dataset import ImageGroupOCR, StorageLocation


class Dataset:
    """
    Access dataset related data and manipulate the dataset.
    """

    def __init__(self, client: EncordClientDataset):
        self._client = client
        self._dataset_instance = None

    @property
    def dataset_hash(self) -> str:
        """
        Get the dataset hash (i.e. the Dataset ID).
        """
        dataset_instance = self._get_dataset_instance()
        return dataset_instance.dataset_hash

    @property
    def title(self) -> str:
        dataset_instance = self._get_dataset_instance()
        return dataset_instance.title

    @property
    def description(self) -> str:
        dataset_instance = self._get_dataset_instance()
        return dataset_instance.description

    @property
    def storage_location(self) -> StorageLocation:
        dataset_instance = self._get_dataset_instance()
        return dataset_instance.storage_location

    @property
    def data_rows(self) -> List[DataRow]:
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
        return self._client.get_dataset()

    def upload_video(self, file_path: str):
        """
        Upload video to Encord storage.

        Args:
            self: Encord client object.
            file_path: path to video e.g. '/home/user/data/video.mp4'

        Returns:
            Bool.

        Raises:
            UploadOperationNotSupportedError: If trying to upload to external
                                              datasets (e.g. S3/GPC/Azure)
        """
        return self._client.upload_video(file_path)

    def create_image_group(self, file_paths: Iterable[str], max_workers: Optional[int] = None):
        """
        Create an image group in Encord storage.

        Args:
            self: Encord client object.
            file_paths: a list of paths to images, e.g.
                ['/home/user/data/img1.png', '/home/user/data/img2.png']
            max_workers:
                Number of workers for parallel image upload. If set to None, this will be the number of CPU cores
                available on the machine.

        Returns:
            Bool.

        Raises:
            UploadOperationNotSupportedError: If trying to upload to external
                                              datasets (e.g. S3/GPC/Azure)
        """
        return self._client.create_image_group(file_paths, max_workers)

    def delete_image_group(self, data_hash: str):
        """
        Create an image group in Encord storage.

        Args:
            self: Encord client object.
            data_hash: the hash of the image group you'd like to delete
        """
        return self._client.delete_image_group(data_hash)

    def delete_data(self, data_hashes: List[str]):
        """
        Delete a video/image group from a dataset.

        Args:
            self: Encord client object.
            data_hashes: list of hash of the videos/image_groups you'd like to delete, all should belong to the same
             dataset
        """
        return self._client.delete_data(data_hashes)

    def add_private_data_to_dataset(
        self,
        integration_id: str,
        private_files: Union[str, Dict, Path, TextIO],
        ignore_errors: bool = False,
    ) -> AddPrivateDataResponse:
        """
        Append data hosted on private clouds to existing dataset

        Args:
            integration_id: str
                EntityId of the cloud integration to be used when accessing those files
            private_files:
                A str path or Path object to a json file, json str or python dictionary of the files you wish to add
            ignore_errors: bool, optional
                Ignore individual errors when trying to access the specified files
        Returns:
            add_private_data_response List of DatasetDataInfo objects containing data_hash and title

        """
        return self._client.add_private_data_to_dataset(integration_id, private_files, ignore_errors)

    def re_encode_data(self, data_hashes: List[str]):
        """
        Launches an async task that can re-encode a list of videos.

        Args:
            self: Encord client object.
            data_hashes: list of hash of the videos you'd like to re_encode, all should belong to the same
             dataset
        Returns:
            EntityId(integer) of the async task launched.

        """
        return self._client.re_encode_data(data_hashes)

    def re_encode_data_status(self, job_id: int):
        """
        Returns the status of an existing async task which is aimed at re-encoding videos.

        Args:
            self: Encord client object.
            job_id: id of the async task that was launched to re-encode the videos

        Returns:
            ReEncodeVideoTask: Object containing the status of the task, along with info about the new encoded videos
             in case the task has been completed
        """
        return self._client.re_encode_data_status(job_id)

    def run_ocr(self, image_group_id: str) -> List[ImageGroupOCR]:
        """
        Returns an optical character recognition result for a given image group
        Args:
            image_group_id: the id of the image group in this dataset to run OCR on

        Returns:
            Returns a list of ImageGroupOCR objects representing the text and corresponding coordinates
            found in each frame of the image group
        """
        return self._client.run_ocr(image_group_id)

    def get_cloud_integrations(self) -> List[CloudIntegration]:
        return self._client.get_cloud_integrations()

    def _get_dataset_instance(self):
        if self._dataset_instance is None:
            self._dataset_instance = self.get_dataset()
        return self._dataset_instance
