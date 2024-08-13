from enum import Enum
from typing import Annotated, Literal, Sequence

from pydantic import BaseModel, Field, RootModel

from encord.http.v2.api_client import ApiClient

__all__ = ["MetadataSchema", "MetadataSchemaError", "ClientMetadataSchemaTypeEmbedding"]


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


class ClientMetadataSchemaTypeEmbedding(BaseModel):
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

    def to_simple_str(self) -> Literal["boolean", "datetime", "uuid", "number", "string", "text"]:
        if self.value == "number":
            return "number"
        elif self.value == "varchar":
            return "string"
        elif self.value == "text":
            return "text"
        elif self.value == "boolean":
            return "boolean"
        elif self.value == "datetime":
            return "datetime"
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
            | ClientMetadataSchemaTypeEmbedding
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
    pass


class MetadataSchemaError(RuntimeError):
    pass


class MetadataSchema:
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
        if self._dirty:
            self._api_client.post(
                "organisation/metadata-schema",
                params=None,
                payload=_ClientMetadataSchema(root=self._schema),
                result_type=None,
            )
            self._dirty = False

    def add_embedding(self, k: str, *, size: int) -> None:
        if k in self._schema:
            raise MetadataSchemaError(f"{k} is already defined")
        self._schema[k] = _ClientMetadataSchemaOption(root=ClientMetadataSchemaTypeEmbedding(size=size))
        self._dirty = True

    def set_simple(self, k: str, *, metadata_type: Literal["boolean", "datetime", "uuid"]) -> None:
        if k in self._schema:
            v = self._schema[k]
            if not isinstance(v.root, _ClientMetadataSchemaTypeVariant):
                raise MetadataSchemaError(f"{k} is already defined")
        self._schema[k] = _ClientMetadataSchemaOption(
            root=_ClientMetadataSchemaTypeVariant(hint=_ClientMetadataSchemaTypeVariantHint(metadata_type))
        )
        self._dirty = True

    def keys(self) -> Sequence[str]:
        return list(self._schema.keys())

    def get_metadata(
        self, k: str
    ) -> ClientMetadataSchemaTypeEmbedding | Literal["boolean", "datetime", "uuid", "number", "string", "text"]:
        if k not in self._schema:
            raise MetadataSchemaError(f"{k} is not defined")
        v = self._schema[k]
        if isinstance(v, ClientMetadataSchemaTypeEmbedding):
            return v
        elif isinstance(v, _ClientMetadataSchemaTypeVariant):
            return v.hint.to_simple_str()
        else:
            raise MetadataSchemaError(f"{k} is not supported in the current SDK")
