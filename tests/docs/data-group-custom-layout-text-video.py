"""
Code Block Name: Create Data Groups
"""

from uuid import UUID
from encord.constants.enums import DataType
from encord.objects.metadata import DataGroupMetadata
from encord.orm.storage import DataGroupCustom
from encord.user_client import EncordUserClient
from encord.orm.storage import StorageItemType

# --- Configuration ---
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt" # Replace with the file path to your SSH key
FOLDER_ID = "82c73d29-8db0-4690-899e-b7e5e623b8e0" # Replace with the Folder ID
PROJECT_ID = "520911af-1245-4793-b798-55e0f407d1e9" # Replace with the Project ID
DATASET_ID = "c3bcf3a2-3928-4975-a8f5-210e645f8135" # Replace with the Dataset ID


# --- Connect to Encord ---
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

folder = user_client.get_storage_folder(FOLDER_ID)

# --- Reusable layout and settings ---
layout = {
    "direction": "column",
    "first": {"type": "data_unit", "key": "instructions"},
    "second": {
        "direction": "column",
        "first": {
            "direction": "row",
            "first": {"type": "data_unit", "key": "top-left"},
            "second": {"type": "data_unit", "key": "top-right"},
            "splitPercentage": 50,
        },
        "second": {
            "direction": "row",
            "first": {"type": "data_unit", "key": "bottom-left"},
            "second": {"type": "data_unit", "key": "bottom-right"},
            "splitPercentage": 50,
        },
        "splitPercentage": 50,
    },
    "splitPercentage": 20,
}
settings = {"tile_settings": {"instructions": {"is_read_only": True}}}

# --- List of data groups with specific UUIDs per tile ---
groups = [
    {
        "name": "group-01",
        "uuids": {
            "instructions": UUID("4b5fb04c-4626-4a6b-86bc-09ea6a6893f8"), # Data unit ID for text file or PDF
            "top-left": UUID("0d36238a-2759-42c3-8e4e-a788f9425ee4"), # Data unit ID for image, video, or audio file
            "top-right": UUID("62fff5b4-df82-43fe-84b7-1bcfc090c14e"), # Data unit ID for image, video, or audio file
            "bottom-left": UUID("e69352c6-e1db-4b4a-a9d7-0fde9fc84cf1"), # Data unit ID for image, video, or audio file
            "bottom-right": UUID("a8b61faf-f5dd-4543-ac15-f1e95328c15c"), # Data unit ID for image, video, or audio file
        },
    },
    {
        "name": "group-02",
        "uuids": {
            "instructions": UUID("209ecfc2-73fc-414c-8627-3ad7eb542e49"), # Data unit ID for text file or PDF
            "top-left": UUID("2a88145a-e8a5-4c68-a9f1-c34b32f24d62"), # Data unit ID for image, video, or audio file
            "top-right": UUID("88ee8731-25de-4571-8822-78d4ecfc2dde"), # Data unit ID for image, video, or audio file
            "bottom-left": UUID("7ebfbd65-965a-49f7-926b-108b594f8d63"), # Data unit ID for image, video, or audio file
            "bottom-right": UUID("20983fbf-666e-4626-b1e3-fc3c206313c1"), # Data unit ID for image, video, or audio file
        },
    },
    # More groups...
]

for g in groups:
    group = folder.create_data_group(
        DataGroupCustom(
            name=g["name"],
            layout=layout,
            layout_contents=g["uuids"],
            settings=settings,
        )
    )
    print(f"✅ Created group '{g['name']}' with UUID {group}")

# Add all the data groups in a folder to a dataset
group_items = folder.list_items(item_types=[StorageItemType.GROUP])
d = user_client.get_dataset(DATASET_ID)
d.link_items([item.uuid for item in group_items])

p = user_client.get_project(PROJECT_ID)
rows = p.list_label_rows_v2(include_children=True)

# label rows of data groups have a "metadata" attribute
for row in rows:
    if row.data_type == DataType.GROUP:
        row.initialise_labels()
        assert isinstance(row.metadata, DataGroupMetadata)
        print(row.metadata.children)


