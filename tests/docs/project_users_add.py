"""
Code Block Name: Add users to Project
"""

# Import dependencies
from encord import EncordUserClient, Project
from encord.utilities.project_user import ProjectUserRole

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"
PROJECT_ID = "f7890e41-6de8-4e66-be06-9fbe182df457"
USER_01 = "example-user-01@encord.com"  # Email addres for user you want to add to Project
USER_02 = "example-user-02@encord.com"  # Email addres for user you want to add to Project
USER_03 = "exmaple-user-02@encord.com"  # Email addres for user you want to add to Project

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Add users by specifying their email addresses, as well as the role these users should have.
added_users = project.add_users(
    [USER_01, USER_02, USER_03],
    # Specify the role the user's have in the Project
    ProjectUserRole.ANNOTATOR,
)

# Print the new users added to the project
print(added_users)
