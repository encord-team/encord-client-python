from encord import EncordUserClient, ProjectManager
from encord.utilities.project_user import ProjectUserRole

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project_manager: ProjectManager = user_client.get_project_manager("<project_hash>")

added_users = project_manager.add_users(
    ["example1@encord.com", "example2@encord.com"],
    ProjectUserRole.ANNOTATOR,
)
print(added_users)
