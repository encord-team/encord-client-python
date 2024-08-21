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
        meta.add_scalar("yolo", hint="embedding")  # type: ignore[arg-type]

    with pytest.raises(MetadataSchemaError):
        meta.add_scalar("embed512", hint="boolean")

    meta.add_scalar("a", hint="number")
    meta.add_scalar("b", hint="boolean")
    meta.add_scalar("c", hint="string")
    meta.add_scalar("d", hint="text")
    meta.add_scalar("e", hint="varchar")
    meta.add_scalar("f", hint="long_string")
    meta.add_scalar("g", hint="long_string")
    meta.add_scalar("a", hint="long_string")
    meta.add_scalar("g", hint="number")

    meta.delete_key("g")

    meta.add_enum("en", values=["h"])
    assert meta.get_enum_options("en") == ["h"]

    meta.add_enum_options("en", values=["h2"])
    assert meta.get_enum_options("en") == ["h", "h2"]

    with pytest.raises(MetadataSchemaError):
        meta.add_scalar("en", hint="boolean")

    assert (
        f"{meta}".strip()
        == """
Metadata Schema:
----------------
 - 'a':        scalar(hint=text)
 - 'b':        scalar(hint=boolean)
 - 'c':        scalar(hint=varchar)
 - 'd':        scalar(hint=text)
 - 'e':        scalar(hint=varchar)
 - 'embed512': embedding(size=512)
 - 'en':       enum(values=['h', 'h2'])
 - 'f':        scalar(hint=text)
    """.strip()
    )
