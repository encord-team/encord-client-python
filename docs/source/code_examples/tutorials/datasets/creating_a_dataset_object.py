from encord import Dataset, EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")

dataset: Dataset = user_client.get_dataset("<dataset_hash>")
