"""
Code Block Name: Data Groups - Get Child Ids from Storage Folder
"""

from encord import EncordUserClient

SSH_PATH="/Users/chris-encord/ssh-private-key.txt" # Replace with the file path to your SSH private key
DATA_GROUP_ID="00000000-0000-0000-0000-000000000000" # Replace with the file ID for the Data Group

# Initialize the SDK client
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Fetch the Data Group as a storage item
data_group_item = user_client.get_storage_item(DATA_GROUP_ID)

print(f"Data Group: {data_group_item.name} ({data_group_item.uuid})")

for item in data_group_item.get_child_items():
    print(f"- UUID: {item.uuid}, Name: {item.name}")