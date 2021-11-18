from enum import Enum


class ObjectShape(Enum):
    POLYGON = 'polygon'
    BOUNDING_BOX = 'bounding_box'
    KEY_POINT = 'point'

    @staticmethod
    def fromString(value: str):
        for objectType in ObjectShape:
            if objectType.value == value:
                return objectType
        return None
