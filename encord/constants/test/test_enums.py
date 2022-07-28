from encord.constants.enums import DataType


def test_data_type_consistency() -> None:
    values_from_string = set()
    for value in DataType:
        string_representation = value.to_upper_case_string()
        value_from_string = DataType.from_upper_case_string(string_representation)
        values_from_string.add(value_from_string)
        assert value == value_from_string

    assert len(values_from_string) == len(DataType)
