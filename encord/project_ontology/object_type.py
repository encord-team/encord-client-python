from enum import Enum


class ObjectShape(Enum):
    POLYGON = "polygon"
    POLYLINE = "polyline"
    BOUNDING_BOX = "bounding_box"
    KEY_POINT = "point"
    SKELETON = "skeleton"
