from encord import Dataset, EncordUserClient
from encord.client import EncordClientDataset

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>",
)

NEW_TIMEOUT = 300  # seconds

# The same procedure works for the Project class that is returned from
# `user_client.get_project("<project_hash>")
dataset: Dataset = user_client.get_dataset("<dataset_hash>")
dataset._client._config.read_timeout = NEW_TIMEOUT
dataset._client._config.write_timeout = NEW_TIMEOUT
dataset._client._config.connect_timeout = NEW_TIMEOUT

# If you are using the deprecated EncordClientDataset instead
dataset_client: EncordClientDataset = user_client.get_dataset_client(
    "<dataset_hash>"
)
dataset_client._config.read_timeout = NEW_TIMEOUT
dataset_client._config.write_timeout = NEW_TIMEOUT
dataset_client._config.connect_timeout = NEW_TIMEOUT
