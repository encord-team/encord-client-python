from typing import Dict, List

from encord.user_client import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

datasets: List[Dict] = user_client.get_datasets()
print(datasets)
