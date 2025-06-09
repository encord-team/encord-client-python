"""
Code Block Name: Create Project
"""

# Import dependencies
from encord.user_client import EncordUserClient

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_TITLE = "My Project 01"
DATASET_ID_01 = "00000000-0000-0000-0000-000000000000"
DATASET_ID_02 = "00000000-0000-0000-0000-000000000000"
DATASET_ID_03 = "00000000-0000-0000-0000-000000000000"
WORKFLOW_TEMPLATE_ID = "00000000-0000-0000-0000-000000000000"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Create a project
project = user_client.create_project(
    project_title=PROJECT_TITLE,
    dataset_hashes=[DATASET_ID_01, DATASET_ID_02, DATASET_ID_03],
    workflow_template_hash=WORKFLOW_TEMPLATE_ID,
)

# Prints the Project ID of the Project you just created
print(project)
