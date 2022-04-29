********
Datasets
********

.. toctree::
    :maxdepth: 2

    creating_a_dataset
    creating_dataset_api_keys

..
    ---
    id: datasets
    title: Datasets
    sidebar_label: Datasets
    ---


    ## Fetching dataset API keys

    Via the Python SDK you can get all API keys for an existing dataset.
    You need to provide the `resource_id` which uniquely identifies a dataset.
    This capability is available to only the Admin of a dataset.

    ```py

    from encord.user_client import EncordUserClient

    user_client = EncordUserClient.create_with_ssh_private_key(
        <YOUR_PRIVATE_KEY>)

    user_client.get_dataset_api_key(
        <RESOURCE_ID>)

    ```

    ```py

    # For example this call will create a dataset, its corresponding API key and then fetch the same.

    from encord.user_client import EncordUserClient
    from encord.orm.dataset import DatasetType

    user_client = EncordUserClient.create_with_ssh_private_key(
        <YOUR_PRIVATE_KEY>)

    dataset = user_client.create_dataset(
        "Traffic Data",
        DatasetType.AWS)

    dataset_api_key: DatasetAPIKey = user_client.create_dataset_api_key(
        dataset.get('dataset_hash'),
        "Full Access API Key",
        [DatasetScope.READ, DatasetScope.WRITE])

    dataset_api_keys: List[DatasetAPIKey] = user_client.get_dataset_api_keys(
        dataset.get('dataset_hash'))

    print(dataset_api_keys)

    # Prints
    # [ DatasetAPIKey(
    #	dataset_hash='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    #	api_key='lCuoabcdefabcdefabcdefabcdefabcdefabc-jlan8',
    #	title='Full Access API Key',
    #	scopes=[
    #        <DatasetScope.READ: 'dataset.read'>,
    #        <DatasetScope.WRITE: 'dataset.write'>]) ]

    ```

    ## Interacting with a dataset

    The Python SDK allows you to interact with the datasets you have added to Encord. A dataset has the attributes `title`, `description`, `dataset_type`, and `data_rows`.

    ```py

    {
        'title': 'sample_dataset_title',
        'description': 'sample_dataset_description',
        'dataset_type': 'sample_dataset_type',
        'data_rows': [{
            'data_hash': 'sample_data_uid',
            'data_title': 'sample_data.mp4',
            'data_type': 'VIDEO'
        }, {
            'data_hash': ...,
        }],
    }

    ```

    Before you start, make sure that a data client is initialised with the appropriate dataset `resource_id` and API key.

    ```py

    from encord.client import EncordClient

    client = EncordClient.initialise(
        <RESOURCE_ID>,
        <DATASET_API_KEY>)

    ```

    ## Adding data

    You can add data to datasets created using the Web App

    ### Adding data to Encord-hosted storage

    #### Uploading videos

    Use the method `client.upload_video(file_path)` to upload data to a dataset using Encord storage.

    ```py

    client.upload_video(
        'sample/video/path.mp4')

    ```

    This will upload the given video file to the client initialised dataset.

    #### Creating image groups

    Use the method `client.create_image_group([file_path_1, file_path_2, ...])` to upload images and create an image group using Encord storage.

    ```py

    client.create_image_group(
        ['sample/image/path1.jpeg',
         'sample/image/path2.jpeg'. ...])

    ```

    This will upload the given list of images to the client initialised dataset and create an image group.

    ### Adding data from private cloud

    1.  Use the `client.get_cloud_integrations()` method to retrieve a list of available Cloud Integrations
    2.  Grab the id from the integration of your choice and call `client.add_private_data_to_dataset(integration_id, file)` where `file` is either the absolute path to a json file or a python dictionary in the format specified in the <a href="/docs/datasets/private-cloud-integration">private cloud section</a> of the datasets documentation

    ```py
    from encord.client import EncordClient
    from encord.orm.dataset import AddPrivateDataResponse
    from encord.orm.dataset import DatasetDataInfo
    from typing import List
    from encord.orm.cloud_integration import CloudIntegration

    client = EncordClient.initialise(
        <RESOURCE_ID>,
        <DATASET_API_KEY>)

    integrations: List[CloudIntegration] = client.get_cloud_integrations()
    integration = integrations[<INDEX_OF_SELECTED_INTEGRATION>].id

    response: AddPrivateDataResponse = client.add_private_data_to_dataset(integration, <FILE>)
    data_info_list: List[DatasetDataInfo] = response.dataset_data_list

    for data_info in data_info_list:
        print(data_info.data_hash)
        print(data_info.title)

    ```

    ## Deleting Data

    You can remove both Videos and Image Groups from datasets created using the Web App.

    Use the method `client.delete_data([data_hash_list])` to delete from a dataset.

    ```py

    client.delete_data(
        ['video1_data_hash',
         'image_group1_data_hash'. ...])

    ```

    In case the Video or ImageGroup belongs to Encord-hosted storage the corresponding file shall be removed from the Encord-hosted storage.

    Please ensure that the list contains Videos/ImageGroups from the same dataset which is used to initialise the EncordClient. Any Videos/ImageGroups which do not belong to the dataset used for initialisation would be ignored.


    ## ReEncoding Videos

    ### Trigger a ReEncoding Task

    You can ReEncode a list of Videos by triggering a task for the same using this API.

    Use the method `client.re_encode_data([data_hash_list])` to re-encode the list of videos specified.

     ```py

    task_id = client.re_encode_data(
        ['video1_data_hash',
         'video2_data_hash'. ...])

    ```

    On completion a task_id(integer) value is returned which can be used for monitoring the progress of the task.

    Please ensure that the list contains Videos from the same dataset which is used to initialise the EncordClient. Any Videos which do not belong to the dataset used for initialisation would be ignored.


    ### Check status of a ReEncoding Task

    You can monitor the status of an existing ReEncoding Task using this API.

    Use the method `client.re_encode_data_status(task_id)` to get the status.

     ```py

    task: ReEncodeVideoTask = client.re_encode_data_status(91)

    ```

    The ReEncodeVideoTask contains a field called 'status' which can take the values

    - 'SUBMITTED' means that the task is currently in progress and the status should be checked back again later.
    - 'DONE' means that the task has completed successfully and the field 'result' would contain metadata about the re-encoded video.
    - 'ERROR' signifies that the task has failed and could not complete the re-encoding.