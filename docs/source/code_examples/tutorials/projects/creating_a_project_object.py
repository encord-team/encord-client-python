from encord import EncordUserClient, Project

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

project: Project = user_client.get_project("<project_hash>")
