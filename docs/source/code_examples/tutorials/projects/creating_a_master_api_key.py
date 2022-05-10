from encord.user_client import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

api_key: str = user_client.get_or_create_project_api_key(
    "<project_hash>",
)
print(api_key)
