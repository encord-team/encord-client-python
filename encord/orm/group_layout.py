from __future__ import annotations

from typing import Dict, Optional, Union
from uuid import UUID

from encord.orm.base_dto import BaseDTO

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore[assignment]


class TileSettings(BaseDTO):
    """Settings for a single tile in a group layout.

    Args:
        title: Optional title displayed in the toolbar for this tile.
        is_read_only: If True, the tile is read-only and no annotations can be added to it.
    """

    title: Optional[str] = None
    is_read_only: bool = False


class LayoutSettings(BaseDTO):
    """Settings for a group layout.

    Args:
        fixed_layout: If True, the layout is fixed and panes cannot be added/removed or changed.
        tile_settings: Optional mapping from tile keys to their settings.
    """

    fixed_layout: bool = False
    tile_settings: Optional[Dict[str, TileSettings]] = None


class DataUnitTile(BaseDTO):
    """A tile containing a single data unit.

    Args:
        type: The tile type, always "data_unit".
        key: The key referencing a data unit in the layout_contents.
    """

    type: Literal["data_unit"] = "data_unit"
    key: str


class DataUnitCarouselTile(BaseDTO):
    """A tile containing a list of data units displayed as a carousel.

    Args:
        type: The tile type, always "data_unit_list".
        keys: List of keys referencing data units in the layout_contents.
        carousel_position: Position of the carousel relative to the main content.
        carousel_size: Initial percentage of the carousel width/height (10-70).
    """

    type: Literal["data_unit_list"] = "data_unit_list"
    keys: list[str]
    carousel_position: Literal["left", "right", "top", "bottom"]
    carousel_size: float


class LayoutGrid(BaseDTO):
    """A grid layout splitting the view into two parts.

    Args:
        direction: The split direction, either "row" (horizontal) or "column" (vertical).
        first: The first part of the split (can be a nested grid or a tile).
        second: The second part of the split (can be a nested grid or a tile).
        split_percentage: The percentage of space allocated to the first part (5-95).
    """

    direction: Literal["row", "column"]
    first: Union["LayoutGrid", DataUnitTile, DataUnitCarouselTile]
    second: Union["LayoutGrid", DataUnitTile, DataUnitCarouselTile]
    split_percentage: float


DataGroupLayout = Union[LayoutGrid, DataUnitCarouselTile]


class StorageItemGroupChild(BaseDTO):
    """Information about a child item in a group layout.

    Args:
        uuid: UUID of the child storage item.
    """

    uuid: UUID


class DataGroupData(BaseDTO):
    """Data about a data group including its layout and child items.

    Args:
        layout_contents: Mapping from layout keys to child item UUIDs.
        layout: The layout structure of the data group.
        layout_settings: Settings for the layout.
    """

    layout_contents: Dict[str, StorageItemGroupChild]
    layout: DataGroupLayout
    layout_settings: LayoutSettings
