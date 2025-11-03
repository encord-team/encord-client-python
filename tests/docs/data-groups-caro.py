from uuid import UUID

from encord.constants.enums import DataType
from encord.objects.metadata import DataGroupMetadata
from encord.orm.storage import DataGroupList, StorageItemType
from encord.user_client import EncordUserClient

# --- Configuration ---
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with the file path to your SSH key
FOLDER_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the Folder ID
DATASET_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the Dataset ID
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the Project ID

# --- Connect to Encord ---
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

folder = user_client.get_storage_folder(FOLDER_ID)

# --- Group definitions (name + UUID list) ---
groups = [
    {
        "name": "group-caro-001",
        "uuids": [
            UUID(
                "00000000-0000-0000-0000-000000000000"
            ),  # Replace with File ID. This data unit appears first in the carousel.
            UUID(
                "11111111-1111-1111-1111-111111111111"
            ),  # Replace with File ID. This data unit appears second in the carousel.
            UUID(
                "22222222-2222-2222-2222-222222222222"
            ),  # Replace with File ID. This data unit appears third in the carousel.
            UUID(
                "33333333-3333-3333-3333-333333333333"
            ),  # Replace with File ID. This data unit appears fourth in the carousel.
        ],
    },
    {
        "name": "group-caro-002",
        "uuids": [
            UUID(
                "44444444-4444-4444-4444-444444444444"
            ),  # Replace with File ID. This data unit appears first in the carousel.
            UUID(
                "55555555-5555-5555-5555-555555555555"
            ),  # Replace with File ID. This data unit appears second in the carousel.
            UUID(
                "66666666-6666-6666-6666-666666666666"
            ),  # Replace with File ID. This data unit appears third in the carousel.
            UUID(
                "77777777-7777-7777-7777-777777777777"
            ),  # Replace with File ID. This data unit appears fourth in the carousel.
        ],
    },
    {
        "name": "group-caro-003",
        "uuids": [
            UUID(
                "88888888-8888-8888-8888-888888888888"
            ),  # Replace with File ID. This data unit appears first in the carousel.
            UUID(
                "99999999-9999-9999-9999-999999999999"
            ),  # Replace with File ID. This data unit appears second in the carousel.
            UUID(
                "12312312-3123-1231-2312-312312312312"
            ),  # Replace with File ID. This data unit appears third in the carousel.
            UUID(
                "45645645-6456-4564-5645-645645645645"
            ),  # Replace with File ID. This data unit appears fourth in the carousel.
        ],
    },
    # Add more groups as needed...
]

# --- Create the data groups using default list layout ---
for g in groups:
    group = folder.create_data_group(
        DataGroupList(
            name=g["name"],
            layout_contents=g["uuids"],
        )
    )
    print(f"✅ Created carousel-layout group '{g['name']}' with UUID {group}")

# --- Add all the data groups in a folder to a dataset ---
group_items = folder.list_items(item_types=[StorageItemType.GROUP])
d = user_client.get_dataset(DATASET_ID)
d.link_items([item.uuid for item in group_items])

# --- Retrieve and inspect data group label rows ---
p = user_client.get_project(PROJECT_ID)
rows = p.list_label_rows_v2(include_children=True)

for row in rows:
    if row.data_type == DataType.GROUP:
        row.initialise_labels()
        assert isinstance(row.metadata, DataGroupMetadata)
        print(row.metadata.children)
