"""
Code Block Name: Create a group and assign it to a Project
"""

# Import dependencies
from encord import EncordUserClient
from encord.utilities.project_user import ProjectUserRole

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
GROUP_NAME = "Reviewers"
GROUP_DESCRIPTION = "Users responsible for reviewing labels"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Create a new group in your organization
group = user_client.create_group(GROUP_NAME, GROUP_DESCRIPTION)

# Open the Project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Assign the group to the Project, specifying the role members of the group will have
project.add_group(group.group_hash, ProjectUserRole.REVIEWER)

# Print the groups now assigned to the Project
print(list(project.list_groups()))
