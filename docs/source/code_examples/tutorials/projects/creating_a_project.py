from encord.user_client import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)

project_hash: str = user_client.create_project(
    "Example project title",
    ["<dataset_hash_1>", "<dataset_hash_2>"],
    "Example project description",
)
print(project_hash)
