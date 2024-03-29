from encord import EncordUserClient
from encord.orm.dataset import DatasetAPIKey

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

dataset_api_key: DatasetAPIKey = user_client.get_or_create_dataset_api_key(
    "<dataset_hash>"
)
print(dataset_api_key)
