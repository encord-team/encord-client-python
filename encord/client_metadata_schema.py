from typing import Dict

import encord.orm.client_metadata_schema as orm
from encord.http.v2.api_client import ApiClient


def set_client_metadata_schema_from_dict(
    api_client: ApiClient, organisation_id: int, json_dict: Dict[str, orm.ClientMetadataSchemaTypes]
) -> None:
    try:
        validated_dict = {key: orm.ClientMetadataSchemaTypes(val) for key, val in json_dict.items()}
    except ValueError:
        raise NotImplementedError(
            f"Got an unexpected data type in schema. Valid data types are: "
            f"{', '.join([v for v in orm.ClientMetadataSchemaTypes])}."
        )
    payload = orm.ClientMetadataSchemaPayload(metadata_schema=validated_dict)
    api_client.post(
        f"organisation/{organisation_id}/client-metadata-schema", params=None, payload=payload, result_type=None
    )
    return


def get_client_metadata_schema(
    api_client: ApiClient, organisation_id: int
) -> dict[str, orm.ClientMetadataSchemaTypes] or None:
    client_metadata_schema = api_client.get(
        f"organisation/{organisation_id}/client-metadata-schema", params=None, result_type=orm.ClientMetadataSchema
    )
    return client_metadata_schema.metadata_schema if client_metadata_schema else None
