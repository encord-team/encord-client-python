"""
Code Block Name: Data Groups - Get Child Ids from Dataset
"""

from uuid import UUID

from encord import EncordUserClient

SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with the file path to your SSH private key
DATA_GROUP_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the file ID for the Data Group
DATASET_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the ID for the Dataset

# Initialize the SDK client
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Data Group
data_group_item = user_client.get_storage_item(DATA_GROUP_ID)
children = list(data_group_item.get_child_items())

# Dataset rows
dataset = user_client.get_dataset(DATASET_ID)
rows = list(dataset.list_data_rows())
rows_by_backing = {}
for r in rows:
    try:
        # Normalize to UUID for robust matching
        if r.backing_item_uuid is not None:
            rows_by_backing[UUID(str(r.backing_item_uuid))] = r
    except Exception:
        pass  # ignore malformed ids

# Print header + ALL children in the group
print(f"Data Group: {data_group_item.name} ({data_group_item.uuid})")
for it in children:
    _row = rows_by_backing.get(UUID(str(it.uuid)))
    print(f"- UUID: {it.uuid}, Name: {it.name}")
