from encord.user_client import EncordUserClient

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project_client = user_client.get_project_client(
    "<project_hash>"
)

project_hash = project_client.copy_project(
    copy_datasets=True,
    copy_collaborators=True,
    copy_models=False,  # Not strictly needed
)
print(project_hash)
