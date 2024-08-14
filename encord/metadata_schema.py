from enum import Enum
from typing import Literal, Sequence
from typing_extensions import Annotated

from pydantic import BaseModel, Field, RootModel

from encord.http.v2.api_client import ApiClient

__all__ = ["MetadataSchema", "MetadataSchemaError"]


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


class _ClientMetadataSchemaOption(
    RootModel[
        Annotated[
            _ClientMetadataSchemaTypeNumber
            | _ClientMetadataSchemaTypeBoolean
            | _ClientMetadataSchemaTypeVarChar
            | _ClientMetadataSchemaTypeDateTime
            | _ClientMetadataSchemaTypeEnum
            | _ClientMetadataSchemaTypeEmbedding
            | _ClientMetadataSchemaTypeText
            | _ClientMetadataSchemaTypeUUID
            | _ClientMetadataSchemaTypeVariant
            | _ClientMetadataSchemaTypeUser,
            Field(discriminator="ty"),
        ]
    ]
):
    pass


class _ClientMetadataSchema(RootModel[dict[str, _ClientMetadataSchemaOption]]):
    """
    Internal type for a metadata schema.
    """

    pass


class MetadataSchemaError(RuntimeError):
    """
    Raised when an invariant is violated when mutating metadata schemas
    """

    pass


class MetadataSchema:
    """
    A class to manage the metadata schema for an organization.
    Methods:
    --------
    save() -> None
        Saves the metadata schema to the backend if it has been modified.
    """

    _dirty: bool
    _schema: dict[str, _ClientMetadataSchemaOption]
    _api_client: ApiClient

    def __init__(self, api_client: ApiClient) -> None:
        self._api_client = api_client
        schema_opt: _ClientMetadataSchema = api_client.get(
            "organisation/metadata-schema",
            params=None,
            result_type=_ClientMetadataSchema,
            allow_none=True,
        )
        self._schema = schema_opt.root if schema_opt is not None else {}
        self._dirty = False

    def save(self) -> None:
        """
        Saves the metadata schema to the backend if changes have been made.
        """
        if self._dirty:
            self._api_client.post(
                "organisation/metadata-schema",
                params=None,
                payload=_ClientMetadataSchema(root=self._schema),
                result_type=None,
            )
            self._dirty = False

    def add_embedding(self, k: str, *, size: int) -> None:
        """
        Adds a new embedding to the metadata schema.
        Parameters:
        -----------
        k : str
            The key under which the embedding will be stored in the schema.
        size : int
            The size of the embedding.
        Raises:
        -------
        MetadataSchemaError
            If the key `k` is already defined in the schema.
        """
        if k in self._schema:
            raise MetadataSchemaError(f"{k} is already defined")
        self._schema[k] = _ClientMetadataSchemaOption(root=_ClientMetadataSchemaTypeEmbedding(size=size))
        self._dirty = True

    def set_key_schema(
        self,
        k: str,
        *,
        metadata_type: Literal["boolean", "datetime", "number", "uuid", "text", "varchar", "string", "long_string"],
    ) -> None:
        """
        Sets a simple metadata type for a given key in the schema.
        Parameters:
        -----------
        k : str
            The key for which the metadata type is being set.
        metadata_type : Literal[
            "boolean", "datetime", "number", "uuid",
            "text", "varchar", "string", "long_string"
        ]
            The type of metadata to be associated with the key. Must be a valid identifier.
        Raises:
        -------
        MetadataSchemaError
            If the key `k` is already defined in the schema with a conflicting type.
        """
        if k in self._schema:
            v = self._schema[k]
            if not isinstance(v.root, _ClientMetadataSchemaTypeVariant):
                raise MetadataSchemaError(f"{k} is already defined")
        self._schema[k] = _ClientMetadataSchemaOption(
            root=_ClientMetadataSchemaTypeVariant(hint=_ClientMetadataSchemaTypeVariantHint(metadata_type))
        )
        self._dirty = True

    def keys(self) -> Sequence[str]:
        """
        Returns a sequence of all keys defined in the metadata schema.
        Returns:
        --------
        Sequence[str]
            A list of keys present in the metadata schema.
        """
        return list(self._schema.keys())

    def get_key_type(self, k: str) -> Literal["boolean", "datetime", "uuid", "number", "varchar", "text", "embedding"]:
        """
        Retrieves the metadata type associated with a given key.
        Parameters:
        -----------
        k : str
            The key for which the metadata type is to be retrieved.
        Returns:
        --------
        Literal["boolean", "datetime", "uuid", "number", "varchar", "text", "embedding"]
            The metadata type associated with the key `k`.
        Raises:
        -------
        MetadataSchemaError
            If the key `k` is not defined in the schema or is not supported by the current SDK.
        """
        if k not in self._schema:
            raise MetadataSchemaError(f"{k} is not defined")
        v = self._schema[k].root
        if isinstance(v, _ClientMetadataSchemaTypeEmbedding):
            return "embedding"
        elif isinstance(v, _ClientMetadataSchemaTypeVariant):
            return v.hint.to_simple_str()
        else:
            raise MetadataSchemaError(f"{k} is not supported in the current SDK")

    def get_embedding_size(self, k: str) -> int:
        """
        Retrieves size associated with a given embedding.
        Parameters:
        -----------
        k : str
            The key for which the metadata type is to be retrieved.
        Returns:
        --------
        int
            The size of the embedding
        Raises:
        -------
        MetadataSchemaError
            If the key `k` is not defined in the schema or is not an embedding
        """
        if k not in self._schema:
            raise MetadataSchemaError(f"{k} is not defined")
        v = self._schema[k].root
        if isinstance(v, _ClientMetadataSchemaTypeEmbedding):
            return v.size
        else:
            raise MetadataSchemaError(f"{k} does not refer to an embedding")
