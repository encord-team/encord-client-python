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
        meta.set_key_schema_hint("yolo", schema="embedding")  # type: ignore[arg-type]

    meta.set_key_schema_hint("a", schema="number")
    meta.set_key_schema_hint("b", schema="boolean")
    meta.set_key_schema_hint("c", schema="string")
    meta.set_key_schema_hint("d", schema="text")
    meta.set_key_schema_hint("e", schema="varchar")
    meta.set_key_schema_hint("f", schema="long_string")
    meta.set_key_schema_hint("g", schema="long_string")
    meta.set_key_schema_hint("a", schema="long_string")
    meta.set_key_schema_hint("g", schema="number")

    meta.delete_key("g")

    meta.add_enum("en", values=["h"])
    assert meta.get_enum_options("en") == ["h"]

    meta.add_enum_options("en", values=["h2"])
    assert meta.get_enum_options("en") == ["h", "h2"]
