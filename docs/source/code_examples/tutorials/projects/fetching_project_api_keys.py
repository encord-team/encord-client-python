from encord.user_client import EncordUserClient

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
api_keys = user_client.get_project_api_keys(
    "<project_hash>"
)
print(api_keys)
