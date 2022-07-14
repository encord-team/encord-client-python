from typing import List

from encord import EncordUserClient
from encord.orm.dataset import DatasetAPIKey

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

keys: List[DatasetAPIKey] = user_client.get_dataset_api_keys("<dataset_hash>")
print(keys)
