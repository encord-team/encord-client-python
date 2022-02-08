from typing import Optional

from encord.orm.project import StringEnum


class DataType(StringEnum):
    VIDEO = "video"
    IMG_GROUP = "img_group"

    @staticmethod
    def from_upper_case_string(string: str) -> Optional["DataType"]:
        if string == "VIDEO":
            return DataType.VIDEO
        elif string == "IMG_GROUP":
            return DataType.IMG_GROUP
        else:
            return None

    def to_upper_case_string(self) -> str:
        return self.value.upper()
