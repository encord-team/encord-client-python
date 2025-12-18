from pydantic import BaseModel


class GeospatialCoordinates(BaseModel):
    latitude: float
    longitude: float
