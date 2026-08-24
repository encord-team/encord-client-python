from enum import Enum
from typing import List, Literal, Optional, Tuple, Union

from pydantic import Field
from typing_extensions import Annotated

from encord.beta.scene._settings_model import SceneSettingsModel as _SceneSettingsModel
from encord.beta.scene._settings_model import hex_color_field


class SceneColorMode(str, Enum):
    HEIGHT = "height"
    PROVIDED = "provided"
    SOLID = "solid"
    IMAGE_COLOR = "imageColor"
    SENSOR = "sensor"


class SceneHeightColouring(_SceneSettingsModel):
    color_mode: Annotated[
        Literal[SceneColorMode.HEIGHT],
        Field(description="Colours points by their vertical position."),
    ] = SceneColorMode.HEIGHT
    color_height_bounds: Annotated[
        Optional[Tuple[float, float]],
        Field(description="Minimum and maximum heights used for the colour gradient."),
    ] = None


class SceneProvidedColouring(_SceneSettingsModel):
    color_mode: Annotated[
        Literal[SceneColorMode.PROVIDED],
        Field(description="Uses colours provided by the point cloud."),
    ] = SceneColorMode.PROVIDED
    display_point_intensity: Annotated[
        Optional[bool],
        Field(description="Whether point intensity modulates the rendered colours."),
    ] = None
    srgb_colors: Annotated[
        Optional[bool],
        Field(description="Whether provided point colours are interpreted as sRGB."),
    ] = None


class SceneSolidColouring(_SceneSettingsModel):
    color_mode: Annotated[
        Literal[SceneColorMode.SOLID],
        Field(description="Uses a single colour for all points."),
    ] = SceneColorMode.SOLID
    display_point_intensity: Annotated[
        Optional[bool],
        Field(description="Whether point intensity modulates the rendered colours."),
    ] = None


class SceneImageColouring(_SceneSettingsModel):
    color_mode: Annotated[
        Literal[SceneColorMode.IMAGE_COLOR],
        Field(description="Colours points by projecting camera images onto them."),
    ] = SceneColorMode.IMAGE_COLOR
    display_point_intensity: Annotated[
        Optional[bool],
        Field(description="Whether point intensity modulates the rendered colours."),
    ] = None


class SceneSensorColouring(_SceneSettingsModel):
    color_mode: Annotated[
        Literal[SceneColorMode.SENSOR],
        Field(description="Uses a different colour for each sensor."),
    ] = SceneColorMode.SENSOR
    display_point_intensity: Annotated[
        Optional[bool],
        Field(description="Whether point intensity modulates the rendered colours."),
    ] = None


ScenePointCloudColouring = Annotated[
    Union[
        SceneHeightColouring,
        SceneProvidedColouring,
        SceneSolidColouring,
        SceneImageColouring,
        SceneSensorColouring,
    ],
    Field(discriminator="color_mode", description="How point cloud points are coloured."),
]


class SceneRadiusIndicator(_SceneSettingsModel):
    frame_of_reference_id: Annotated[
        str,
        Field(description="Frame of reference at the centre of the radius indicator."),
    ]
    radius: Annotated[float, Field(ge=0, description="Radius of the indicator in scene units.")]
    color: Annotated[str, hex_color_field()]


class SceneViewSettings(_SceneSettingsModel):
    point_cloud_colouring: Optional[ScenePointCloudColouring] = None
    point_radius: Annotated[
        Optional[float],
        Field(ge=0, le=100, description="Radius used to render point cloud points."),
    ] = None
    render_image_outside_base_range: Annotated[
        Optional[bool],
        Field(description="Whether images outside the scene's base time range are rendered."),
    ] = None
    radius_indicators: Annotated[
        Optional[List[SceneRadiusIndicator]],
        Field(description="Radius indicators displayed in the scene."),
    ] = None
    radius_filter_enabled: Annotated[
        Optional[bool],
        Field(description="Whether point clouds are filtered to the configured radius indicators."),
    ] = None
