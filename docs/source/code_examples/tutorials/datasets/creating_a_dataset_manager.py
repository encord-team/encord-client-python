from encord import DatasetManager, EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")

dataset_manager: DatasetManager = user_client.get_dataset_manager("<dataset_hash>")
