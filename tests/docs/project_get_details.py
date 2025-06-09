"""
Code Block Name: View Project details
"""

# Import dependencies
from encord import EncordUserClient

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Prints relevant Project information
print(f"Project Title: {project.title}")
print(f"Description: {project.description}")
print(f"Created at: {project.created_at}")
print(f"Ontology ID: {project.ontology_hash}")
print(f"Datasets: {project.list_datasets()}")
print(f"Workflow: {project.workflow.stages}")
