import json
from enum import Enum
from typing import Dict, Literal, Sequence, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from encord.http.v2.api_client import ApiClient

__all__ = ["MetadataSchema", "MetadataSchemaError"]

from encord.orm.base_dto import RootModelDTO


class _NumberFormat(Enum):
    F32 = "F32"
    F64 = "F64"


class _ClientMetadataSchemaTypeNumber(BaseModel):
    ty: Literal["number"] = "number"
    format: _NumberFormat = _NumberFormat.F64


class _ClientMetadataSchemaTypeBoolean(BaseModel):
    ty: Literal["boolean"] = "boolean"


class _ClientMetadataSchemaTypeVarChar(BaseModel):
    ty: Literal["varchar"] = "varchar"
    max_length: int = Field(8192, ge=0, le=8192)


class _ClientMetadataSchemaTypeDateTime(BaseModel):
    ty: Literal["datetime"] = "datetime"
    timezone: Literal["UTC"] = "UTC"


class _ClientMetadataSchemaTypeEnum(BaseModel):
    ty: Literal["enum"] = "enum"
    values: Sequence[str] = Field([], min_length=1, max_length=256)


class _ClientMetadataSchemaTypeEmbedding(BaseModel):
    ty: Literal["embedding"] = "embedding"
    size: int = Field(gt=0, le=4096)


class _ClientMetadataSchemaTypeText(BaseModel):
    ty: Literal["text"] = "text"


class _ClientMetadataSchemaTypeUUID(BaseModel):
    ty: Literal["uuid"] = "uuid"


class _ClientMetadataSchemaTypeVariantHint(Enum):
    NUMBER = "number"
    VARCHAR = "varchar"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    UUID = "uuid"

    def to_simple_str(self) -> Literal["boolean", "datetime", "uuid", "number", "varchar", "text", "uuid"]:
        if self.value == "number":
            return "number"
        elif self.value == "varchar":
            return "varchar"
        elif self.value == "text":
            return "text"
        elif self.value == "boolean":
            return "boolean"
        elif self.value == "datetime":
            return "datetime"
        elif self.value == "uuid":
            return "uuid"
        else:
            raise ValueError(f"Unknown simple type: {self}")

    @classmethod
    def _missing_(cls, value):
        if value in ("text", "long_string"):
            return cls.TEXT
        elif value in ("varchar", "string"):
            return cls.VARCHAR

        raise ValueError("Unknown simple schema type")


class _ClientMetadataSchemaTypeVariant(BaseModel):
    ty: Literal["variant"] = "variant"
    hint: _ClientMetadataSchemaTypeVariantHint = _ClientMetadataSchemaTypeVariantHint.TEXT


class _ClientMetadataSchemaTypeUser(BaseModel):
    ty: Literal["user"] = "user"


class _ClientMetadataSchemaTypeTombstone(BaseModel):
    ty: Literal["tombstone"] = "tombstone"


class _ClientMetadataSchemaOption(
    RootModelDTO[
        Annotated[
            Union[
                _ClientMetadataSchemaTypeNumber,
                _ClientMetadataSchemaTypeBoolean,
                _ClientMetadataSchemaTypeVarChar,
                _ClientMetadataSchemaTypeDateTime,
                _ClientMetadataSchemaTypeEnum,
                _ClientMetadataSchemaTypeEmbedding,
                _ClientMetadataSchemaTypeText,
                _ClientMetadataSchemaTypeUUID,
                _ClientMetadataSchemaTypeVariant,
                _ClientMetadataSchemaTypeUser,
                _ClientMetadataSchemaTypeTombstone,
            ],
            Field(discriminator="ty"),
        ]
    ]
):
    pass


class _ClientMetadataSchema(RootModelDTO[Dict[str, _ClientMetadataSchemaOption]]):
    """
    Internal type for a metadata schema.
    """

    pass


class MetadataSchemaError(RuntimeError):
    """
    Raised when an invariant is violated when mutating metadata schemas
    """

    pass


def _is_valid_metadata_key(value: str) -> bool:
    if value.startswith("$") or value == "":
        return False
    for extra_char in ["-", "_", " ", "."]:
        value = value.replace(extra_char, "")
    if value == "":
        return False
    # deprecated special-keys
    if value in ("keyframes",):
        return False
    return value.isalnum()


def _assert_valid_metadata_key(value: str) -> None:
    if not _is_valid_metadata_key(value):
        raise MetadataSchemaError(f"{value} is an invalid format for a metadata key")


class MetadataSchema:
    """
    A class to manage the metadata schema for an organization.

    **Methods:**

    save() -> None: Saves the metadata schema to the backend if it has been modified.
    """

    _dirty: bool
    _schema: Dict[str, _ClientMetadataSchemaOption]
    _api_client: ApiClient

    def __init__(self, api_client: ApiClient) -> None:
        self._api_client = api_client
        schema_opt: _ClientMetadataSchema = api_client.get(  # type: ignore[type-var]
            "organisation/client-metadata-schema-v2",
            params=None,
            result_type=_ClientMetadataSchema,  # type: ignore[arg-type]
            allow_none=True,
        )
        self._schema = schema_opt.root if schema_opt is not None else {}  # type: ignore[assignment]
        self._dirty = False

    def save(self) -> None:
        """
        Saves the metadata schema to the backend if changes have been made.
        """
        if self._dirty:
            self._api_client.post(
                "organisation/client-metadata-schema-v2",
                params=None,
                payload=_ClientMetadataSchema.model_validate(self._schema),  # type: ignore[arg-type]
                result_type=None,
            )
            self._dirty = False

    def add_embedding(self, k: str, *, size: int) -> None:
        """
        Adds a new embedding to the metadata schema.

        **Parameters:**

        - k : str: The key under which the embedding will be stored in the schema.
        - size : int: The size of the embedding.

        **Raises:**

        MetadataSchemaError: If the key `k` is already defined in the schema.
        """
        if k in self._schema:
            raise MetadataSchemaError(f"{k} is already defined")
        _assert_valid_metadata_key(k)
        self._schema[k] = _ClientMetadataSchemaOption(root=_ClientMetadataSchemaTypeEmbedding(size=size))
        self._dirty = True

    def add_enum(self, k: str, *, values: Sequence[str]) -> None:
        """
        Adds a new enum to the metadata schema.

        **Parameters:**

        - k : str: The key under which the embedding will be stored in the schema.
        - values : Sequence[str]: The set of values for the enum (min 1, max 256).

        **Raises:**

        MetadataSchemaError: If the key `k` is already defined in the schema.
        """
        if k in self._schema:
            raise MetadataSchemaError(f"{k} is already defined")
        _assert_valid_metadata_key(k)
        if len(values) == 0:
            raise MetadataSchemaError("Must provide at least 1 value")
        elif len(values) >= 256:
            raise MetadataSchemaError("Cannot provide more than 256 values")
        self._schema[k] = _ClientMetadataSchemaOption(root=_ClientMetadataSchemaTypeEnum(values=sorted(values)))
        self._dirty = True

    def add_enum_options(self, k: str, *, values: Sequence[str]) -> None:
        """
        Adds extra valid enum values to an existing enum schema.

        **Parameters:**

        - k : str: The key referencing the enum.
        - values : Sequence[str]: The set of new values to add to the enum (min 1, max 256).

        **Raises:**

        MetadataSchemaError: If the key `k` is not defined in the schema or is not an enum.
        """
        if k not in self._schema:
            raise MetadataSchemaError(f"{k} is already defined")
        _assert_valid_metadata_key(k)
        v = self._schema[k].root
        if not isinstance(v, _ClientMetadataSchemaTypeEnum):
            raise MetadataSchemaError(f"{k} is not an enum")
        new_values = list(v.values) + list(values)
        if len(new_values) == 0 or len(values) == 0:
            raise MetadataSchemaError("Must provide at least 1 value")
        elif len(new_values) >= 256:
            raise MetadataSchemaError("Cannot provide more than 256 values")
        self._schema[k] = _ClientMetadataSchemaOption(root=_ClientMetadataSchemaTypeEnum(values=sorted(new_values)))
        self._dirty = True

    def add_scalar(
        self,
        k: str,
        *,
        data_type: Literal["boolean", "datetime", "number", "uuid", "text", "varchar", "string", "long_string"],
    ) -> None:
        """
        Sets a simple metadata type for a given key in the schema.

        **Parameters:**

        - k : str: The key for which the metadata type is being set.
        - schema : Literal["boolean", "datetime", "number", "uuid", "text", "varchar", "string", "long_string"]
                   The type of metadata to be associated with the key. Must be a valid identifier.
                   "string" is an alias of "varchar"
                   "long_string" is an alias of "text"

        **Raises:**

        MetadataSchemaError: If the key `k` is already defined in the schema with a conflicting type.
        """
        if k in self._schema:
            v = self._schema[k]
            if not isinstance(v.root, _ClientMetadataSchemaTypeVariant):
                raise MetadataSchemaError(f"{k} is already defined")
        _assert_valid_metadata_key(k)
        if data_type == "embedding":
            raise MetadataSchemaError("Embedding must be created explicitly")
        elif data_type == "enum":
            raise MetadataSchemaError("Enum must be created explicitly")
        self._schema[k] = _ClientMetadataSchemaOption(
            root=_ClientMetadataSchemaTypeVariant(hint=_ClientMetadataSchemaTypeVariantHint(data_type))
        )
        self._dirty = True

    def delete_key(self, k: str) -> None:
        """
        Delete a metadata key from the schema, this cannot be undone.

        **Parameters:**

        k : str: The key for which the metadata type is being deleted.

        **Raises:**

        MetadataSchemaError: If the key `k` is already deleted or not present in the schema
        """
        if k in self._schema:
            v = self._schema[k]
            if isinstance(v.root, _ClientMetadataSchemaTypeTombstone):
                raise MetadataSchemaError(f"{k} is already deleted")
        else:
            raise MetadataSchemaError(f"{k} is not defined")
        _assert_valid_metadata_key(k)
        self._schema[k] = _ClientMetadataSchemaOption(root=_ClientMetadataSchemaTypeTombstone())
        self._dirty = True

    def keys(self) -> Sequence[str]:
        """
        Returns a sequence of all keys defined in the metadata schema.

        **Returns:**

        Sequence[str]: A list of keys present in the metadata schema.
        """
        return list(self._schema.keys())

    def has_key(self, k: str) -> bool:
        """
        Check if any definition exists for a key.

        **Parameters:**

        k : str: The key for which the metadata type is to be retrieved.
        """
        return k in self._schema

    def is_key_deleted(self, k: str) -> bool:
        """
        Check if the key is defined as deleted. (Tombstone type)

        **Parameters:**

        k : str: The key for which the metadata type is to be retrieved.
        """
        if k not in self._schema:
            return False
        _assert_valid_metadata_key(k)
        v = self._schema[k].root
        return isinstance(v, _ClientMetadataSchemaTypeTombstone)

    def get_key_type(
        self, k: str
    ) -> Union[Literal["boolean", "datetime", "uuid", "number", "varchar", "text", "embedding", "enum"], None]:
        """
        Retrieves the metadata type associated with a given key.

        **Parameters:**

        k : str: The key for which the metadata type is to be retrieved.

        **Returns:**

        Literal["boolean", "datetime", "uuid", "number", "varchar", "text", "embedding", "enum"]: The metadata type associated with the key `k`.

        Raises:

        MetadataSchemaError: If the key `k` is not supported by the current SDK.
        """
        if k not in self._schema:
            return None
        _assert_valid_metadata_key(k)
        v = self._schema[k].root
        if isinstance(v, _ClientMetadataSchemaTypeEmbedding):
            return "embedding"
        elif isinstance(v, _ClientMetadataSchemaTypeEnum):
            return "enum"
        elif isinstance(v, _ClientMetadataSchemaTypeVariant):
            return v.hint.to_simple_str()
        elif isinstance(v, _ClientMetadataSchemaTypeTombstone):
            return None
        elif isinstance(v, _ClientMetadataSchemaTypeBoolean):
            return "boolean"
        elif isinstance(v, _ClientMetadataSchemaTypeNumber):
            return "number"
        elif isinstance(v, _ClientMetadataSchemaTypeDateTime):
            return "datetime"
        elif isinstance(v, _ClientMetadataSchemaTypeVarChar):
            return "varchar"
        elif isinstance(v, _ClientMetadataSchemaTypeText):
            return "text"
        elif isinstance(v, _ClientMetadataSchemaTypeUUID):
            return "uuid"
        else:
            raise MetadataSchemaError(f"{k} is not supported in the current SDK")

    def get_embedding_size(self, k: str) -> int:
        """
        Retrieves size associated with a given embedding.

        **Parameters:**

        k : str: The key for which the metadata type is to be retrieved.

        **Returns:**

        int: The size of the embedding

        **Raises:**

        MetadataSchemaError: If the key `k` is not defined in the schema or is not an embedding
        """
        if k not in self._schema:
            raise MetadataSchemaError(f"{k} is not defined")
        _assert_valid_metadata_key(k)
        v = self._schema[k].root
        if isinstance(v, _ClientMetadataSchemaTypeEmbedding):
            return v.size
        else:
            raise MetadataSchemaError(f"{k} does not refer to an embedding")

    def get_enum_options(self, k: str) -> Sequence[str]:
        """
        Retrieves all values associated with a given enum.

        **Parameters:**

        k : str: The key for which the metadata type is to be retrieved.

        **Returns:**

        Sequence[str]: The list of all values associated with an enum type.

        **Raises:**

        MetadataSchemaError: If the key `k` is not defined in the schema or is not an enum.
        """
        if k not in self._schema:
            raise MetadataSchemaError(f"{k} is not defined")
        _assert_valid_metadata_key(k)
        v = self._schema[k].root
        if isinstance(v, _ClientMetadataSchemaTypeEnum):
            return sorted(v.values)
        else:
            raise MetadataSchemaError(f"{k} does not refer to an enum")

    def __repr__(self):
        return json.dumps({k: self._schema[k].model_dump(mode="json") for k in sorted(self._schema.keys())})

    def __str__(self) -> str:
        schema = "Metadata Schema:\n"
        schema += "----------------\n"
        max_length = max([len(k) for k in self._schema.keys()], default=0)
        for k in sorted(self._schema.keys()):
            v = self._schema[k].root
            ty_hint_str: str
            padding: str = " " * (max_length - len(k))
            if isinstance(v, _ClientMetadataSchemaTypeEmbedding):
                ty_hint_str = f"embedding(size={v.size})"
            elif isinstance(v, _ClientMetadataSchemaTypeEnum):
                ty_hint_str = f"enum(values={sorted(v.values)})"
            elif isinstance(v, _ClientMetadataSchemaTypeVariant):
                ty_hint_str = f"scalar(hint={v.hint.to_simple_str()})"
            elif isinstance(v, _ClientMetadataSchemaTypeTombstone):
                continue
            elif isinstance(v, _ClientMetadataSchemaTypeBoolean):
                ty_hint_str = "boolean"
            elif isinstance(v, _ClientMetadataSchemaTypeNumber):
                ty_hint_str = "number"
            elif isinstance(v, _ClientMetadataSchemaTypeDateTime):
                ty_hint_str = "datetime"
            elif isinstance(v, _ClientMetadataSchemaTypeVarChar):
                ty_hint_str = "varchar"
            elif isinstance(v, _ClientMetadataSchemaTypeText):
                ty_hint_str = "text"
            elif isinstance(v, _ClientMetadataSchemaTypeUUID):
                ty_hint_str = "uuid"
            else:
                raise MetadataSchemaError(f"{k} is not supported in the current SDK")
            schema += f" - '{k}': {padding}{ty_hint_str}\n"

        return schema
