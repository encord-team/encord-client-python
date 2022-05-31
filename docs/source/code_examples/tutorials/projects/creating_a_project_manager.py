from encord import EncordUserClient, ProjectManager

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")

project_manager: ProjectManager = user_client.get_project_manager("<dataset_hash>")
