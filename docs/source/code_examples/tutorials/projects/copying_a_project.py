from encord.client import EncordClientProject
from encord.user_client import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project_client: EncordClientProject = user_client.get_project_client(
    "<project_hash>"
)

project_hash: str = project_client.copy_project(
    copy_datasets=True,
    copy_collaborators=True,
    copy_models=False,  # Not strictly needed
)
print(project_hash)
