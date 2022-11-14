import dataclasses


@dataclasses.dataclass
class DatasetSettings:
    """Settings for using the dataset object."""

    fetch_client_metadata: bool
    """Whether client metadata should be retrieved for each data_row."""


DEFAULT_DATASET_SETTINGS = DatasetSettings(
    fetch_client_metadata=False,
)
