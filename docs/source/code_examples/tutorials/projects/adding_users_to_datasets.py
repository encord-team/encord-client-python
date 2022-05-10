from encord.user_client import EncordUserClient
from encord.utilities.project_user import ProjectUserRole

user_client = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project_client = user_client.get_project_client(
    "<project_hash>",
)

added_users = project_client.add_users(
    ["example1@encord.com", "example2@encord.com"],
    ProjectUserRole.ANNOTATOR,
)
print(added_users)
