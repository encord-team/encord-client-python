from encord.user_client import EncordUserClient

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
datasets = user_client.get_datasets()
print(datasets)
