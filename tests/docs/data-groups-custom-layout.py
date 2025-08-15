"""
Code Block Name: Data Groups - Custom Layout
"""

from uuid import UUID

from encord.constants.enums import DataType
from encord.objects.metadata import DataGroupMetadata
from encord.orm.storage import DataGroupCustom, StorageItemType
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

# --- Group definitions (name + UUIDs) ---
groups = [
    {
        "name": "group-001",
        "uuids": {
            "instructions": UUID(
                "00000000-0000-0000-0000-000000000000"
            ),  # Replace with File ID. This data unit appears at the top of the Label Editor.
            "top-left": UUID(
                "11111111-1111-1111-1111-111111111111"
            ),  # Replace with File ID. This data unit appears under the "instructions" data unit at the top left of the Label Editor.
            "top-right": UUID(
                "22222222-2222-2222-2222-222222222222"
            ),  # Replace with File ID. This data unit appears under the "instructions" data unit at the top right of the Label Editor.
            "bottom-left": UUID(
                "33333333-3333-3333-3333-333333333333"
            ),  # Replace with File ID. This data unit appears under the top left data unit in the Label Editor.
            "bottom-right": UUID(
                "44444444-4444-4444-4444-444444444444"
            ),  # Replace with File ID. This data unit appears under the top right data unit in the Label Editor.
        },
    },
    {
        "name": "group-002",
        "uuids": {
            "instructions": UUID(
                "55555555-5555-5555-5555-555555555555"
            ),  # Replace with File ID. This data unit appears at the top of the Label Editor.
            "top-left": UUID(
                "66666666-6666-6666-6666-666666666666"
            ),  # Replace with File ID. This data unit appears under the "instructions" data unit at the top left of the Label Editor.
            "top-right": UUID(
                "77777777-7777-7777-7777-777777777777"
            ),  # Replace with File ID. This data unit appears under the "instructions" data unit at the top right of the Label Editor.
            "bottom-left": UUID(
                "88888888-8888-8888-8888-888888888888"
            ),  # Replace with File ID. This data unit appears under the top left data unit in the Label Editor.
            "bottom-right": UUID(
                "99999999-9999-9999-9999-999999999999"
            ),  # Replace with File ID. This data unit appears under the top right data unit in the Label Editor.
        },
    },
    {
        "name": "group-003",
        "uuids": {
            "instructions": UUID(
                "12312312-3123-1231-2312-312312312312"
            ),  # Replace with File ID. This data unit appears at the top of the Label Editor.
            "top-left": UUID(
                "23232323-2323-2323-2323-232323232323"
            ),  # Replace with File ID. This data unit appears under the "instructions" data unit at the top left of the Label Editor.
            "top-right": UUID(
                "31313131-3131-3131-3131-313131313131"
            ),  # Replace with File ID. This data unit appears under the "instructions" data unit at the top right of the Label Editor.
            "bottom-left": UUID(
                "45645645-6456-4564-5645-645645645645"
            ),  # Replace with File ID. This data unit appears under the top left data unit in the Label Editor.
            "bottom-right": UUID(
                "56565656-6565-5656-6565-656565656565 "
            ),  # Replace with File ID. This data unit appears under the top right data unit in the Label Editor.
        },
    },
    # More groups...
]

# Create the data groups

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

# Add all the data groups in a folder to a Dataset
group_items = folder.list_items(item_types=[StorageItemType.GROUP])
d = user_client.get_dataset(DATASET_ID)
d.link_items([item.uuid for item in group_items])

# Add the Dataset with the Data Groups to a Project

p = user_client.get_project(PROJECT_ID)
rows = p.list_label_rows_v2(include_children=True)

# Label Rows of Data Groups use DataGroupMetadata for the layout to Annotate and Review
for row in rows:
    if row.data_type == DataType.GROUP:
        row.initialise_labels()
        assert isinstance(row.metadata, DataGroupMetadata)
        print(row.metadata.children)
