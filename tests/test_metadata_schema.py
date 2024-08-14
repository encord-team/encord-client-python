from unittest.mock import MagicMock

import pytest

from encord.metadata_schema import MetadataSchema, MetadataSchemaError


def test_metadata_schema() -> None:
    meta = MetadataSchema(MagicMock())
    meta._schema = {}
    assert meta.keys() == []
    meta.add_embedding("embed512", size=512)
    assert meta.keys() == ["embed512"]
    assert meta.get_key_type("embed512") == "embedding"
    assert meta.get_embedding_size("embed512") == 512

    with pytest.raises(MetadataSchemaError):
        meta.set_key_schema("yolo", schema="embedding")  # type: ignore[arg-type]

    meta.set_key_schema("a", schema="number")
    meta.set_key_schema("b", schema="boolean")
    meta.set_key_schema("c", schema="string")
    meta.set_key_schema("d", schema="text")
    meta.set_key_schema("e", schema="varchar")
    meta.set_key_schema("f", schema="long_string")
    meta.set_key_schema("g", schema="long_string")
    meta.set_key_schema("a", schema="long_string")
    meta.set_key_schema("g", schema="number")
