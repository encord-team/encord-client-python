import json
import uuid
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime
import encord.orm.client_metadata_schema as orm
from encord.http.v2.api_client import ApiClient


class ClientMetadataSchema:

    def __init__(self, api_client: ApiClient, client_metadata_schema: orm.ClientMetadataSchema | None):
        self._api_client = api_client
        self._client_metadata_schema = client_metadata_schema

    @property
    def uuid(self) -> UUID:
        return self._client_metadata_schema.uuid

    @property
    def metadata_schema(self) -> Dict[str, orm.ClientMetadataSchemaTypes]:
        return self._client_metadata_schema.metadata_schema

    @property
    def organisation_id(self) -> int:
        return self._client_metadata_schema.organisation_id

    def set_metadata_schema_from_dict(self, json_dict: Dict[str, orm.ClientMetadataSchemaTypes]) -> None:
        try:
            validated_dict = {key: orm.ClientMetadataSchemaTypes(val) for key, val in json_dict.items()}
        except ValueError:
            raise NotImplementedError(
                f"Got an unexpected data type in schema. Valid data types are: "
                f"{', '.join([v for v in orm.ClientMetadataSchemaTypes])}.")
        self._client_metadata_schema.metadata_schema = validated_dict

    def save(self) -> None:
        payload = orm.ClientMetadataSchemaPayload(metadata_schema=self._client_metadata_schema.metadata_schema)
        return self._api_client.post(
            f"organisation/{self._client_metadata_schema.organisation_id}/client-metadata-schema",
            params=None,
            payload=payload,
            result_type=None
        )

    @staticmethod
    def _get_client_metadata_schema(api_client: ApiClient, organisation_id: int) -> "ClientMetadataSchema":
        client_metadata_schema = api_client.get(
            f"organisation/{organisation_id}/client-metadata-schema", params=None, result_type=orm.ClientMetadataSchema
        )
        if client_metadata_schema.organisation_id == -1:
            client_metadata_schema.organisation_id = organisation_id
        return ClientMetadataSchema(api_client, client_metadata_schema)
