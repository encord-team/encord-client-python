from encord.client import EncordClientProject
from encord.user_client import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project_client: EncordClientProject = user_client.get_project_client(
    "<project_hash>"
)

success: bool = project_client.remove_datasets(
    [
        "<dataset_hash1>",
        "<dataset_hash2>",
        # ...
    ]
)
print(success)
