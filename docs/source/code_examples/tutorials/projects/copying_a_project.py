from encord import EncordUserClient, ProjectManager

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project_manager: ProjectManager = user_client.get_project_manager("<project_hash>")


project_hash: str = project_manager.copy_project(
    copy_datasets=True,
    copy_collaborators=True,
    copy_models=False,  # Not strictly needed
)
print(project_hash)
