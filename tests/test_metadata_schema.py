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
        meta.add_dynamic("yolo", ty="embedding")  # type: ignore[arg-type]

    with pytest.raises(MetadataSchemaError):
        meta.add_dynamic("embed512", ty="boolean")

    meta.add_dynamic("a", ty="number")
    meta.add_dynamic("b", ty="boolean")
    meta.add_dynamic("c", ty="string")
    meta.add_dynamic("d", ty="text")
    meta.add_dynamic("e", ty="varchar")
    meta.add_dynamic("f", ty="long_string")
    meta.add_dynamic("g", ty="long_string")
    meta.add_dynamic("a", ty="long_string")
    meta.add_dynamic("g", ty="number")

    meta.delete_key("g")

    meta.add_enum("en", values=["h"])
    assert meta.get_enum_options("en") == ["h"]

    meta.add_enum_options("en", values=["h2"])
    assert meta.get_enum_options("en") == ["h", "h2"]

    with pytest.raises(MetadataSchemaError):
        meta.add_dynamic("en", ty="boolean")

    assert (
        f"{meta}".strip()
        == """
Metadata Schema:
----------------
 - 'a':        dynamic(hint=text)
 - 'b':        dynamic(hint=boolean)
 - 'c':        dynamic(hint=varchar)
 - 'd':        dynamic(hint=text)
 - 'e':        dynamic(hint=varchar)
 - 'embed512': embedding(size=512)
 - 'en':       enum(values=['h', 'h2'])
 - 'f':        dynamic(hint=text)
    """.strip()
    )
