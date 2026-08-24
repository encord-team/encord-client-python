import pytest
from pydantic import ValidationError

from encord.beta.scene import (
    Scene3DViewerTile,
    SceneImageTile,
    SceneLayout,
    SceneTileLayout,
    SceneTileLayoutDirection,
    SceneTimeSeriesTile,
)
from encord.orm.storage import TimeSeriesLineChannelViewSettings, TimeSeriesViewSettings


def _timeseries_settings() -> TimeSeriesViewSettings:
    return TimeSeriesViewSettings(
        channels={
            "speed": TimeSeriesLineChannelViewSettings(
                label="Speed",
                color="#ffffff",
                hidden=False,
                line_width=2,
            )
        }
    )


def test_scene_layout_serializes_to_api_shape() -> None:
    scene_layout = SceneLayout(
        tiles={
            "0": Scene3DViewerTile(has_side_view=True, show_camera_switcher=False),
            "front": SceneImageTile(stream_name="front_camera"),
            "speed": SceneTimeSeriesTile(
                stream_name="telemetry",
                timeseries_settings=_timeseries_settings(),
            ),
        },
        layout=SceneTileLayout(
            direction=SceneTileLayoutDirection.ROW,
            first="0",
            second="front",
            split_percentage=60,
        ),
        timeline=["speed"],
    )

    assert scene_layout.to_dict() == {
        "tiles": {
            "0": {"type": "3d", "hasSideView": True, "showCameraSwitcher": False},
            "front": {"type": "image", "streamName": "front_camera"},
            "speed": {
                "type": "timeseries",
                "streamName": "telemetry",
                "timeseriesSettings": {
                    "channels": {
                        "speed": {
                            "label": "Speed",
                            "color": "#ffffff",
                            "hidden": False,
                            "style": "line",
                            "lineWidth": 2.0,
                        }
                    }
                },
            },
        },
        "layout": {
            "direction": "row",
            "first": "0",
            "second": "front",
            "splitPercentage": 60.0,
        },
        "timeline": ["speed"],
    }


@pytest.mark.parametrize(
    "scene_layout",
    [
        {
            "tiles": {"viewer": {"type": "3d", "hasSideView": True, "showCameraSwitcher": True}},
            "layout": "viewer",
        },
        {
            "tiles": {"front": {"type": "image", "streamName": "front"}},
            "layout": {"direction": "row", "first": "front", "second": "front"},
        },
        {
            "tiles": {"front": {"type": "image", "streamName": "front"}},
            "layout": "missing",
        },
        {
            "tiles": {"front": {"type": "image", "streamName": "front"}},
            "timeline": ["front"],
        },
    ],
)
def test_scene_layout_rejects_invalid_tile_references(scene_layout: dict) -> None:
    with pytest.raises(ValidationError):
        SceneLayout(**scene_layout)
