from encord import Dataset, EncordUserClient, Project

user_client = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project: Project = user_client.get_project("<project_id>")
dataset: Dataset = user_client.get_dataset("<dataset_id>")
