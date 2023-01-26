import logging
import time

import requests.exceptions

from encord import Dataset, EncordUserClient
from encord.exceptions import EncordException


def upload_item(object_url: str, integration_id: str, dataset: Dataset) -> None:
    """Adding data one by one to a dataset."""
    add_private_data_response = dataset.add_private_data_to_dataset(
        integration_id,
        # Check the https://docs.encord.com/datasets/private-cloud-integration/#json-format documentation to build
        # the correct format for your upload.
        {
            "images": [
                {"objectUrl": object_url},
            ]
        },
    )
    if len(add_private_data_response.dataset_data_list) != 1:
        # If the request returns but there is not item added, there might be something wrong with the uploaded file.
        # You can reach out to the Encord team for support.
        logging.error(
            f"Error adding private data for object_url {object_url}. The add private data response "
            f"was: {add_private_data_response}"
        )


object_urls = [
    "https://bucket/object1.jpeg",
    "https://bucket/object2.jpeg",
]
# TODO: reset these ^

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "YOUR PRIVATE SSH KEY"
)
# TODO: set this ^
dataset: Dataset = user_client.get_dataset("YOUR DATASET RESOURCE ID")
# TODO: set this ^

integration_title = "YOUR INTEGRATION TITLE"  # TODO: set this

integration = None
for available_integration in dataset.get_cloud_integrations():
    if available_integration.title == integration_title:
        integration = available_integration
        break
if integration is None:
    logging.error(
        f"Integration with title {integration_title} not found - aborting"
    )
    exit()

# Set the timeout as uploads of large files can take a long time
TIMEOUT = 60 * 60  # 1 h
dataset._client._config.read_timeout = TIMEOUT
dataset._client._config.write_timeout = TIMEOUT
dataset._client._config.connect_timeout = TIMEOUT

for object_url in object_urls:
    retries = 5
    backoff_seconds = 2
    while retries > 0:
        try:
            upload_item(object_url, integration.id, dataset)
            logging.info(f"Successfully uploaded {object_url}")
            break
        except requests.exceptions.ReadTimeout:
            logging.exception(
                f"Your request timed out. The file with object url {object_url} might be processed in "
                "the background. Check the upload at a later time. Do not retry it for now. You might want to adjust "
                "your set timeout.",
                stack_info=True,
            )
            break
        except EncordException:
            logging.exception(
                f"Caught exception when adding {object_url} to Encord. Sleeping for {backoff_seconds}",
                stack_info=True,
            )
            if retries == 0:
                logging.error(
                    f"All retries exhausted. - Upload for object url {object_url} will be skipped."
                )
                break
            time.sleep(backoff_seconds)
            retries -= 1
            backoff_seconds *= 2
