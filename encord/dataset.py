from pathlib import Path
from typing import Dict, Iterable, List, Optional, TextIO, Union

from encord.client import EncordClientDataset
from encord.http.utils import CloudUploadSettings
from encord.orm.cloud_integration import CloudIntegration
from encord.orm.dataset import AddPrivateDataResponse, DataRow
from encord.orm.dataset import Dataset as OrmDataset
from encord.orm.dataset import (
    DatasetAccessSettings,
    DatasetUser,
    DatasetUserRole,
    Image,
    ImageGroupOCR,
    StorageLocation,
)


class Dataset:
    """
    Access dataset related data and manipulate the dataset.
    """

    def __init__(self, client: EncordClientDataset):
        self._client = client
        self._dataset_instance: Optional[OrmDataset] = None

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
        """
        Part of the response of this function can be configured by the
        :meth:`encord.dataset.Dataset.set_access_settings` method.

        .. code::

            dataset.set_access_settings(DatasetAccessSettings(fetch_client_metadata=True))
            print(dataset.data_rows)
        """
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

    def set_access_settings(self, dataset_access_settings: DatasetAccessSettings, *, refetch_data: bool = True) -> None:
        """
        Args:
            dataset_access_settings: The access settings to use going forward
            refetch_data: Whether a `refetch_data()` call should follow the update of the dataset access settings.
        """
        self._client.set_access_settings(dataset_access_settings)
        if refetch_data:
            self.refetch_data()

    def add_users(self, user_emails: List[str], user_role: DatasetUserRole) -> List[DatasetUser]:
        """
        Add users to dataset. If the user was already added, this operation will succeed but the `user_role` will be
        unchanged. The existing `user_role` will be reflected in the `DatasetUser` instance.

        Args:
            user_emails: list of user emails to be added
            user_role: the user role to assign to all users
        """
        return self._client.add_users(user_emails, user_role)

    def upload_video(
        self,
        file_path: str,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        title: Optional[str] = None,
    ):
        """
        Upload video to Encord storage.

        Args:
            file_path: path to video e.g. '/home/user/data/video.mp4'
            cloud_upload_settings:
                Settings for uploading data into the cloud. Change this object to overwrite the default values.
            title:
                The video title. If unspecified, this will be the file name. This title should include an extension.
                For example "encord_video.mp4".

        Returns:
            Bool.

        Raises:
            UploadOperationNotSupportedError: If trying to upload to external
                                              datasets (e.g. S3/GPC/Azure)
        """
        return self._client.upload_video(file_path, cloud_upload_settings=cloud_upload_settings, title=title)

    def create_image_group(
        self,
        file_paths: Iterable[str],
        max_workers: Optional[int] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        title: Optional[str] = None,
        *,
        create_video: bool = True,
    ):
        """
        Create an image group in Encord storage. Choose this type of image upload for sequential images. Else, you can
        choose the :meth:`.Dataset.upload_image` function.

        Args:
            file_paths: a list of paths to images, e.g.
                ['/home/user/data/img1.png', '/home/user/data/img2.png']
            max_workers:
                DEPRECATED: This argument will be ignored
            cloud_upload_settings:
                Settings for uploading data into the cloud. Change this object to overwrite the default values.
            title:
                The title of the image group. If unspecified this will be randomly generated for you. This title should
                NOT include an extension. For example "encord_image_group".
            create_video:
                A flag specifying how image groups are stored. If `True`, a compressed video will be created from
                the image groups. `True` was the previous default support. If `False`, the images
                are saved as a sequence of images.

        Returns:
            Bool.

        Raises:
            UploadOperationNotSupportedError: If trying to upload to external
                                              datasets (e.g. S3/GPC/Azure)
        """
        return self._client.create_image_group(
            file_paths,
            cloud_upload_settings=cloud_upload_settings,
            title=title,
            create_video=create_video,
        )

    def create_dicom_series(
        self,
        file_paths: List[str],
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
        title: Optional[str] = None,
    ):
        """
        Upload a DICOM series to Encord storage

        Args:
            file_paths: a list of paths to DICOM files, e.g.
                ['/home/user/data/DICOM_1.dcm', '/home/user/data/DICOM_2.dcm']
            cloud_upload_settings:
                Settings for uploading data into the cloud. Change this object to overwrite the default values.
            title:
                The title of the DICOM series. If unspecified this will be randomly generated for you. This title should
                NOT include an extension. For example "encord_image_group".
        Returns:
            Bool.

        Raises:
            UploadOperationNotSupportedError: If trying to upload to external
                                              datasets (e.g. S3/GPC/Azure)
        """
        return self._client.create_dicom_series(file_paths, cloud_upload_settings=cloud_upload_settings, title=title)

    def upload_image(
        self,
        file_path: Union[Path, str],
        title: Optional[str] = None,
        cloud_upload_settings: CloudUploadSettings = CloudUploadSettings(),
    ) -> Image:
        """
        Upload a single image to Encord storage. If your images are sequential we recommend creating an image group via
        the :meth:`.Dataset.create_image_group` function. For more information please compare
        https://docs.encord.com/docs/annotate/editor/images and https://docs.encord.com/docs/annotate/editor/videos

        Args:
            file_path: The file path to the image
            title: The image title. If unspecified, this will be the file name. This title should include an extension.
                For example "encord_image.png".
            cloud_upload_settings:
                Settings for uploading data into the cloud. Change this object to overwrite the default values.

        """
        return self._client.upload_image(file_path, title, cloud_upload_settings)

    def delete_image_group(self, data_hash: str):
        """
        Delete an image group in Encord storage.

        Args:
            data_hash: the hash of the image group to delete
        """
        return self._client.delete_image_group(data_hash)

    def delete_data(self, data_hashes: List[str]):
        """
        Delete a video/image group from a dataset.

        Args:
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
        Append data hosted on private clouds to existing dataset.

        For a more complete example of safe uploads, please follow the guide found in our docs under
        :ref:`https://python.docs.encord.com/tutorials/datasets.html#adding-data-from-a-private-cloud
        <tutorials/datasets:Adding data from a private cloud>`

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

    def update_data_item(self, data_hash: str, new_title: str) -> bool:
        """
        DEPRECATED: Use the individual setter properties of the respective :class:`encord.orm.dataset.DataRow`
        instance instead. These can be retrieved via the :meth:`.Dataset.data_rows` function.

        Update a data item

        Args:
            data_hash: str
                Data hash of the item being updated
            new_title:
                String containing the new title of the data item being updated
        Returns:
           Returns a boolean for whether the update was successful

        """
        return self._client.update_data_item(data_hash, new_title)

    def re_encode_data(self, data_hashes: List[str]):
        """
        Launches an async task that can re-encode a list of videos.

        Args:
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
