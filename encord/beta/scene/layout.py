from __future__ import annotations

from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import Field
from typing_extensions import Annotated

from encord.beta.scene._settings_model import SceneSettingsModel as _SceneLayoutModel
from encord.orm.base_dto import dto_validator
from encord.orm.storage import TimeSeriesViewSettings

MAX_SCENE_TILES = 50
MIN_SPLIT_PERCENTAGE = 5
MAX_SPLIT_PERCENTAGE = 95


class Scene3DViewerTile(_SceneLayoutModel):
    type: Literal["3d"] = "3d"
    has_side_view: Annotated[
        bool,
        Field(description="Whether the 3D viewer includes a side view."),
    ]
    show_camera_switcher: Annotated[
        bool,
        Field(description="Whether the 3D viewer displays the camera switcher."),
    ]


class SceneImageTile(_SceneLayoutModel):
    type: Literal["image"] = "image"
    stream_name: Annotated[
        str,
        Field(min_length=1, description="Name of the composite scene image stream displayed by the tile."),
    ]


class SceneTimeSeriesTile(_SceneLayoutModel):
    type: Literal["timeseries"] = "timeseries"
    stream_name: Annotated[
        str,
        Field(min_length=1, description="Name of the composite scene time-series stream displayed by the tile."),
    ]
    timeseries_settings: Annotated[
        TimeSeriesViewSettings,
        Field(description="Initial rendering settings for the time-series stream."),
    ]


SceneTile = Annotated[
    Union[Scene3DViewerTile, SceneImageTile, SceneTimeSeriesTile],
    Field(discriminator="type"),
]


class SceneTileLayoutDirection(str, Enum):
    ROW = "row"
    COLUMN = "column"


class SceneTileLayout(_SceneLayoutModel):
    direction: Annotated[
        SceneTileLayoutDirection,
        Field(description="Direction in which the two child panes are split."),
    ]
    first: Annotated[
        Union[str, SceneTileLayout],
        Field(description="Tile ID or nested layout in the first pane."),
    ]
    second: Annotated[
        Union[str, SceneTileLayout],
        Field(description="Tile ID or nested layout in the second pane."),
    ]
    split_percentage: Annotated[
        float,
        Field(
            ge=MIN_SPLIT_PERCENTAGE,
            le=MAX_SPLIT_PERCENTAGE,
            description="Percentage of space assigned to the first pane.",
        ),
    ] = 50


class SceneLayout(_SceneLayoutModel):
    tiles: Annotated[
        Dict[str, SceneTile],
        Field(
            min_length=1,
            max_length=MAX_SCENE_TILES,
            description="Tiles available to the scene layout, keyed by tile ID.",
        ),
    ]
    layout: Annotated[
        Optional[Union[str, SceneTileLayout]],
        Field(description="Mosaic layout of tile IDs. May be omitted for a timeline-only layout."),
    ] = None
    timeline: List[str] = Field(
        default_factory=list,
        max_length=MAX_SCENE_TILES,
        description="IDs of time-series tiles displayed in the timeline.",
    )

    @dto_validator(mode="after")
    def validate_tile_references(cls, scene_layout: SceneLayout) -> SceneLayout:
        layout_tile_ids = _collect_layout_tile_ids(scene_layout.layout)
        if len(layout_tile_ids) != len(set(layout_tile_ids)):
            raise ValueError("Layout cannot contain duplicate tile IDs")

        timeline_tile_ids = set(scene_layout.timeline)
        if len(timeline_tile_ids) != len(scene_layout.timeline):
            raise ValueError("Timeline cannot contain duplicate tile IDs")

        tile_ids = set(scene_layout.tiles)
        viewer_tile_ids = [
            tile_id for tile_id, tile in scene_layout.tiles.items() if isinstance(tile, Scene3DViewerTile)
        ]
        if viewer_tile_ids and viewer_tile_ids != ["0"]:
            raise ValueError("The 3D viewer must be the single tile with ID '0'")

        referenced_tile_ids = set(layout_tile_ids) | timeline_tile_ids
        if unknown_tile_ids := referenced_tile_ids - tile_ids:
            raise ValueError(f"Layout references unknown tile IDs: {sorted(unknown_tile_ids)}")

        invalid_timeline_tile_ids = [
            tile_id
            for tile_id in scene_layout.timeline
            if not isinstance(scene_layout.tiles[tile_id], SceneTimeSeriesTile)
        ]
        if invalid_timeline_tile_ids:
            raise ValueError(f"Timeline can contain only time-series tiles: {invalid_timeline_tile_ids}")

        if unused_tile_ids := tile_ids - referenced_tile_ids:
            raise ValueError(f"Layout does not reference tile IDs: {sorted(unused_tile_ids)}")

        return scene_layout


def _collect_layout_tile_ids(layout: Optional[Union[str, SceneTileLayout]]) -> List[str]:
    if layout is None:
        return []
    if isinstance(layout, str):
        return [layout]
    return _collect_layout_tile_ids(layout.first) + _collect_layout_tile_ids(layout.second)
