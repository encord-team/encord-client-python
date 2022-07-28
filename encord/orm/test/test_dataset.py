from typing import Set

from encord.orm.dataset import StorageLocation


def test_storage_location_to_str() -> None:
    unique_representations: Set[StorageLocation] = set()

    for location in StorageLocation:
        string_representation = StorageLocation.get_str(location)
        location_from_string = StorageLocation.from_str(string_representation)

        unique_representations.add(location)

        assert isinstance(string_representation, str)
        assert location == location_from_string

    assert len(unique_representations) == len(StorageLocation)
