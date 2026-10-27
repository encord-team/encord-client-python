"""Per-Scene rendering settings applied by the label editor.

Assign a :class:`SceneViewSettings` to ``SceneBuilder.settings`` before upload, or update a
registered Scene with ``StorageItem.update(scene_view_settings=...)``. Unset fields fall back to
the annotator's own preferences.
"""

from enum import Enum
from typing import List, Literal, Optional, Tuple, Union

from pydantic import Field
from typing_extensions import Annotated

from encord.beta.scene._settings_model import SceneSettingsModel as _SceneSettingsModel
from encord.beta.scene._settings_model import hex_color_field


class SceneColorMode(str, Enum):
    """How point cloud points are colored."""

    HEIGHT = "height"
    PROVIDED = "provided"
    SOLID = "solid"
    IMAGE_COLOR = "imageColor"
    SENSOR = "sensor"


class SceneHeightColouring(_SceneSettingsModel):
    """Color points by their height, using a gradient between ``color_height_bounds``."""

    color_mode: Annotated[
        Literal[SceneColorMode.HEIGHT],
        Field(description="Colors points by their vertical position."),
    ] = SceneColorMode.HEIGHT
    color_height_bounds: Annotated[
        Optional[Tuple[float, float]],
        Field(description="Minimum and maximum heights used for the color gradient."),
    ] = None


class SceneProvidedColouring(_SceneSettingsModel):
    """Color points with the colors stored in the point cloud files."""

    color_mode: Annotated[
        Literal[SceneColorMode.PROVIDED],
        Field(description="Uses colors provided by the point cloud."),
    ] = SceneColorMode.PROVIDED
    display_point_intensity: Annotated[
        Optional[bool],
        Field(description="Whether point intensity modulates the rendered colors."),
    ] = None
    srgb_colors: Annotated[
        Optional[bool],
        Field(description="Whether provided point colors are interpreted as sRGB."),
    ] = None


class SceneSolidColouring(_SceneSettingsModel):
    """Color all points with a single color."""

    color_mode: Annotated[
        Literal[SceneColorMode.SOLID],
        Field(description="Uses a single color for all points."),
    ] = SceneColorMode.SOLID
    display_point_intensity: Annotated[
        Optional[bool],
        Field(description="Whether point intensity modulates the rendered colors."),
    ] = None


class SceneImageColouring(_SceneSettingsModel):
    """Color points by projecting camera images onto them."""

    color_mode: Annotated[
        Literal[SceneColorMode.IMAGE_COLOR],
        Field(description="Colors points by projecting camera images onto them."),
    ] = SceneColorMode.IMAGE_COLOR
    display_point_intensity: Annotated[
        Optional[bool],
        Field(description="Whether point intensity modulates the rendered colors."),
    ] = None


class SceneSensorColouring(_SceneSettingsModel):
    """Color points with a different color for each sensor."""

    color_mode: Annotated[
        Literal[SceneColorMode.SENSOR],
        Field(description="Uses a different color for each sensor."),
    ] = SceneColorMode.SENSOR
    display_point_intensity: Annotated[
        Optional[bool],
        Field(description="Whether point intensity modulates the rendered colors."),
    ] = None


ScenePointCloudColouring = Annotated[
    Union[
        SceneHeightColouring,
        SceneProvidedColouring,
        SceneSolidColouring,
        SceneImageColouring,
        SceneSensorColouring,
    ],
    Field(discriminator="color_mode", description="How point cloud points are colored."),
]


class SceneRadiusIndicator(_SceneSettingsModel):
    """A circle drawn around a frame of reference.

    ``frame_of_reference_id`` must be ``"root"`` (the world frame) or the name of a
    frame-of-reference stream in the same Scene. ``radius`` is in Scene units, and ``color``
    is a hex color such as ``"#FF8A00"``.
    """

    frame_of_reference_id: Annotated[
        str,
        Field(description="Frame of reference at the centre of the radius indicator."),
    ]
    radius: Annotated[float, Field(ge=0, description="Radius of the indicator in scene units.")]
    color: Annotated[str, hex_color_field()]


class SceneViewSettings(_SceneSettingsModel):
    """Rendering settings the label editor applies when it opens the Scene.

    Fields left as ``None`` fall back to the annotator's own preferences.
    """

    point_cloud_colouring: Optional[ScenePointCloudColouring] = None
    point_radius: Annotated[
        Optional[float],
        Field(ge=0, le=100, description="Radius used to render point cloud points."),
    ] = None
    render_image_outside_base_range: Annotated[
        Optional[bool],
        Field(
            description=(
                "Whether to render the full image captured by the camera, instead of clipping the "
                "undistorted image to its original bounds. Useful for wide-angle and fisheye lenses."
            )
        ),
    ] = None
    radius_indicators: Annotated[
        Optional[List[SceneRadiusIndicator]],
        Field(description="Radius indicators displayed in the scene."),
    ] = None
    radius_filter_enabled: Annotated[
        Optional[bool],
        Field(description="Whether point clouds are filtered to the configured radius indicators."),
    ] = None
