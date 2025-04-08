"""
Code Block Name: List all Projects
"""

# Import dependencies
from encord.user_client import EncordUserClient

# User input
SSH_PATH = "/Users/laverne-encord/prod-sdk-ssh-key-private-key.txt"

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# List existing projects
projects = user_client.get_projects()
print(projects)
