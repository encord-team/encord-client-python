from unittest.mock import MagicMock

import pytest

from encord.metadata_schema import MetadataSchema, MetadataSchemaError


def test_root_model() -> None:
    import encord.metadata_schema as metadata_schema

    _ClientMetadataSchema = metadata_schema._ClientMetadataSchema
    _ClientMetadataSchemaOption = metadata_schema._ClientMetadataSchemaOption
    _ClientMetadataSchema.model_validate({})

    a = _ClientMetadataSchema.model_validate({"k": {"ty": "variant", "hint": "number"}})
    assert isinstance(a.root["k"], _ClientMetadataSchemaOption)
    assert a.root["k"].root.hint.value == "number"
    assert a.model_dump(mode="json") == {"k": {"ty": "variant", "hint": "number"}}


def test_metadata_schema() -> None:
    meta = MetadataSchema(MagicMock())
    meta._schema = {}
    assert meta.keys() == []
    meta.add_embedding("embed512", size=512)
    assert meta.keys() == ["embed512"]
    assert meta.get_key_type("embed512") == "embedding"
    assert meta.get_embedding_size("embed512") == 512

    with pytest.raises(MetadataSchemaError):
        meta.add_scalar("yolo", data_type="embedding")  # type: ignore[arg-type]

    with pytest.raises(MetadataSchemaError):
        meta.add_scalar("embed512", data_type="boolean")

    meta.add_scalar("a", data_type="number")
    meta.add_scalar("b", data_type="boolean")
    meta.add_scalar("c", data_type="string")
    meta.add_scalar("d", data_type="text")
    meta.add_scalar("e", data_type="varchar")
    meta.add_scalar("f", data_type="long_string")
    meta.add_scalar("g", data_type="long_string")
    meta.add_scalar("a", data_type="long_string")
    meta.add_scalar("g", data_type="number")
    meta.add_scalar("g", data_type="text")
    meta.add_scalar("g", data_type="number")

    assert meta.has_key("g")
    assert not meta.has_key("g2")
    assert meta.get_key_type("g2") is None

    meta.delete_key("g")
    assert meta.has_key("g")
    assert meta.is_key_deleted("g")
    assert meta.get_key_type("g") is None

    meta.add_enum("en", values=["h"])
    assert meta.get_enum_options("en") == ["h"]

    meta.add_enum_options("en", values=["h2"])
    assert meta.get_enum_options("en") == ["h", "h2"]

    with pytest.raises(MetadataSchemaError):
        meta.add_scalar("en", data_type="boolean")

    meta.add_scalar("a.b", data_type="boolean")

    assert (
        f"{meta}".strip()
        == """
Metadata Schema:
----------------
 - 'a':        scalar(hint=text)
 - 'a.b':      scalar(hint=boolean)
 - 'b':        scalar(hint=boolean)
 - 'c':        scalar(hint=varchar)
 - 'd':        scalar(hint=text)
 - 'e':        scalar(hint=varchar)
 - 'embed512': embedding(size=512)
 - 'en':       enum(values=['h', 'h2'])
 - 'f':        scalar(hint=text)
    """.strip()
    )
