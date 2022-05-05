from typing import List

from encord.orm.dataset import DatasetAPIKey
from encord.user_client import EncordUserClient

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
keys: List[
    DatasetAPIKey
] = user_client.get_dataset_api_keys("<dataset_hash>")

print(keys)
