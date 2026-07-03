"""
Code Block Name: Create a group and add users
"""

# Import dependencies
from encord import EncordUserClient

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
GROUP_NAME = "Annotation Team"
GROUP_DESCRIPTION = "Users responsible for annotating data"
USER_01 = "example-user-01@encord.com"  # Email address for user you want to add to the group
USER_02 = "example-user-02@encord.com"  # Email address for user you want to add to the group

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Create a new group in your organization
group = user_client.create_group(GROUP_NAME, GROUP_DESCRIPTION)
print(f"Created group {group.name} with hash {group.group_hash}")

# Add users to the group by specifying their email addresses.
# Emails that do not yet belong to the organization are invited to it.
group_users = group.add_users([USER_01, USER_02])

# Print the users now in the group
print(group_users)
