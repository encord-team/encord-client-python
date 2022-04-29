from encord.user_client import EncordUserClient
from encord.client import (
    EncordClientProject,
    EncordClientDataset,
)

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project_client: EncordClientProject = (
    user_client.get_project_client("<project_id>")
)
dataset_client: EncordClientDataset = (
    user_client.get_dataset_client("<dataset_id>")
)
