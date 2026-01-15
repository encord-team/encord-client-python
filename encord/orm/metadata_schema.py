from pydantic import BaseModel, Field


class GeospatialCoordinates(BaseModel):
    """Geographic coordinates represented by latitude and longitude.

    This model is used to describe a precise location on the Earth's surface.
    Values are validated to fall within standard geographic bounds.

    Attributes:
        latitude (float): Latitude in degrees, ranging from -90.0 to 90.0.
        longitude (float): Longitude in degrees, ranging from -180.0 to 180.0.
    """

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
