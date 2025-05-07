"""
Code Block Name: Copy Project - Simple
"""

# Import dependencies
from encord import EncordUserClient, Project

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "4b8756eb-eecb-415f-a212-4fb57c95b218"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Copy the Project with attached datasets and collaborators
new_project_id = project.copy_project(
    copy_datasets=True,
    copy_collaborators=True,
    copy_models=False,  # Not strictly needed
)
# Print the new Project's ID
print(new_project_id)
