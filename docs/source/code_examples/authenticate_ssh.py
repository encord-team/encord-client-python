from encord import DatasetManager, EncordUserClient, ProjectManager

user_client = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project_manager: ProjectManager = user_client.get_project_manager("<project_id>")
dataset_manager: DatasetManager = user_client.get_dataset_manager("<dataset_id>")
