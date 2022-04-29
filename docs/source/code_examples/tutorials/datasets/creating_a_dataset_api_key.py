from encord.user_client import EncordUserClient
from encord.orm.dataset import DatasetScope, DatasetAPIKey

user_client = EncordUserClient.create_with_ssh_private_key(
    "<YOUR_PRIVATE_KEY>"
)

dataset_api_key: DatasetAPIKey = (
    user_client.create_dataset_api_key(
        "<dataset_hash>",
        "Full Access API Key",
        [DatasetScope.READ, DatasetScope.WRITE],
    )
)
print(dataset_api_key)
