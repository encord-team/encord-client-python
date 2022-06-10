from encord import EncordUserClient, Project
from encord.utilities.project_user import ProjectUserRole

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project: Project = user_client.get_project("<project_hash>")

added_users = project.add_users(
    ["example1@encord.com", "example2@encord.com"],
    ProjectUserRole.ANNOTATOR,
)
print(added_users)
