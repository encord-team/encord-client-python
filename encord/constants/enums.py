from encord.orm.project import StringEnum


class DataType(StringEnum):
    VIDEO = "video"
    IMG_GROUP = "img_group"
    DICOM = "dicom"
    IMAGE = "image"

    @staticmethod
    def from_upper_case_string(string: str) -> "DataType":
        for data_type in DataType:
            if string == data_type.to_upper_case_string():
                return data_type

        raise ValueError(f"No DataType corresponding to value [{string}]")

    def to_upper_case_string(self) -> str:
        return self.value.upper()
