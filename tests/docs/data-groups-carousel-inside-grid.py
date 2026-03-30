from uuid import UUID


from encord.user_client import EncordUserClient
from encord.orm.storage import DataGroupCustom
from encord.orm.group_layout import (
    LayoutGrid,
    LayoutSettings,
    DataUnitTile,
    DataUnitCarouselTile,
)

# User Input

SSH_PATH = "/path/to/your/encord_private_key.txt"
FOLDER_ID = "00000000-0000-0000-0000-000000000000"
GROUP_NAME = "carousel-inside-grid"


# --- Connect to Encord ---
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

folder = user_client.get_storage_folder(FOLDER_ID)


# Replace these with real file UUIDs

LAYOUT_CONTENTS = {
    "g1": UUID("11111111-1111-1111-1111-111111111111"),
    "g2": UUID("22222222-2222-2222-2222-222222222222"),
    "g3": UUID("33333333-3333-3333-3333-333333333333"),
    "g4": UUID("44444444-4444-4444-4444-444444444444"),
    "g5": UUID("55555555-5555-5555-5555-555555555555"),
    "g6": UUID("66666666-6666-6666-6666-666666666666"),
    "g7": UUID("77777777-7777-7777-7777-777777777777"),
    "g8": UUID("88888888-8888-8888-8888-888888888888"),
    "g9": UUID("99999999-9999-9999-9999-999999999999"),
    "c1": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    "c2": UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    "c3": UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
    "c4": UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
}


# 3x3 grid on the left
row_1 = LayoutGrid(
    direction="row",
    first=DataUnitTile(key="g1"),
    second=LayoutGrid(
        direction="row",
        first=DataUnitTile(key="g2"),
        second=DataUnitTile(key="g3"),
        split_percentage=50,
    ),
    split_percentage=33,
)

row_2 = LayoutGrid(
    direction="row",
    first=DataUnitTile(key="g4"),
    second=LayoutGrid(
        direction="row",
        first=DataUnitTile(key="g5"),
        second=DataUnitTile(key="g6"),
        split_percentage=50,
    ),
    split_percentage=50,
)

row_3 = LayoutGrid(
    direction="row",
    first=DataUnitTile(key="g7"),
    second=LayoutGrid(
        direction="row",
        first=DataUnitTile(key="g8"),
        second=DataUnitTile(key="g9"),
        split_percentage=50,
    ),
    split_percentage=50,
)

grid_3x3 = LayoutGrid(
    direction="column",
    first=row_1,
    second=LayoutGrid(
        direction="column",
        first=row_2,
        second=row_3,
        split_percentage=50,
    ),
    split_percentage=33,
)

# Carousel on the right

carousel_panel = DataUnitCarouselTile(
    keys=["c1", "c2", "c3", "c4"],
    carousel_position="right",
    carousel_size=25,
)

# Final layout

layout = LayoutGrid(
    direction="row",
    first=grid_3x3,
    second=carousel_panel,
    split_percentage=78,
)

settings = LayoutSettings(fixed_layout=True)


group_uuid = folder.create_data_group(
        DataGroupCustom(
            name=GROUP_NAME,
            layout=layout,
            layout_contents=LAYOUT_CONTENTS,
            settings=settings,
        )
    )

print(f"Created data group: {group_uuid}")

