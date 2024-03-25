import json
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime
import encord.orm.client_metadata_schema as orm
from encord.http.v2.api_client import ApiClient


class ClientMetadataSchema:

    def __init__(self, api_client: ApiClient, client_metadata_schema: orm.ClientMetadataSchema):
        self._api_client = api_client
        self._client_metadata_schema = client_metadata_schema

    @property
    def uuid(self) -> UUID:
        return self._client_metadata_schema.uuid

    @property
    def metadata_schema(self) -> Dict[str, orm.ClientMetadataSchemaTypes]:
        return self._client_metadata_schema.metadata_schema

    @property
    def created_at(self) -> datetime:
        return self._client_metadata_schema.created_at

    @property
    def updated_at(self) -> datetime:
        return self._client_metadata_schema.updated_at

    def set_metadata_schema_from_dict(self, json_dict: Dict[str, str]) -> None:
        # get updated dict from json_dict by changing value of every key to key_val
        validated_json_dict = {key: orm.ClientMetadataSchemaTypes(val) for key, val in json_dict.items()}
        self._client_metadata_schema.metadata_schema = validated_json_dict

    def save(self) -> None:
        payload = orm.ClientMetadataSchemaPayload(metadata_schema=self._client_metadata_schema.metadata_schema)
        return self._api_client.post(f"client_metadata_schema", params=None, payload=payload, result_type=None)

    @staticmethod
    def _get_client_metadata_schema(api_client: ApiClient) -> "ClientMetadataSchema":
        client_metadata_schema = api_client.get(
            f"client_metadata_schema", params=None, result_type=orm.ClientMetadataSchema
        )
        return ClientMetadataSchema(api_client, client_metadata_schema)
