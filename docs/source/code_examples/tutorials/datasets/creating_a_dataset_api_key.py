from encord.orm.dataset import DatasetAPIKey, DatasetScope
from encord.user_client import EncordUserClient

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

dataset_api_key: DatasetAPIKey = (
    user_client.create_dataset_api_key(
        "<dataset_hash>",
        "Full Access API Key",
        [DatasetScope.READ, DatasetScope.WRITE],
    )
)
print(dataset_api_key)
