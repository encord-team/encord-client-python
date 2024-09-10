from typing import Dict, Optional

import encord.orm.client_metadata_schema as orm
from encord.common.deprecated import deprecated
from encord.http.v2.api_client import ApiClient


@deprecated("0.1.132")
def set_client_metadata_schema_from_dict(api_client: ApiClient, json_dict: Dict[str, orm.ClientMetadataSchemaTypes]):
    """
    Set the client metadata schema from a dictionary.

    Args:
        api_client (ApiClient): The API client to use for the request.
        json_dict (Dict[str, orm.ClientMetadataSchemaTypes]): A dictionary containing the client metadata schema types.

    Raises:
        NotImplementedError: If an unexpected data type is encountered in the schema.
    """
    try:
        validated_dict = {key: orm.ClientMetadataSchemaTypes(val) for key, val in json_dict.items()}
    except ValueError:
        raise NotImplementedError(
            f"Got an unexpected data type in schema. Valid data types are: "
            f"{', '.join([v for v in orm.ClientMetadataSchemaTypes])}."
        )
    payload = orm.ClientMetadataSchemaPayload(metadata_schema=validated_dict)
    api_client.post("organisation/client-metadata-schema", params=None, payload=payload, result_type=None)


@deprecated("0.1.132")
def get_client_metadata_schema(api_client: ApiClient) -> Optional[Dict[str, orm.ClientMetadataSchemaTypes]]:
    """
    Retrieve the client metadata schema.

    Args:
        api_client (ApiClient): The API client to use for the request.

    Returns:
        Optional[Dict[str, orm.ClientMetadataSchemaTypes]]: A dictionary containing the client metadata schema types
        if available, otherwise None.
    """
    client_metadata_schema: Optional[orm.ClientMetadataSchema] = api_client.get(
        "organisation/client-metadata-schema",
        params=None,
        result_type=orm.ClientMetadataSchema,
        allow_none=True,
    )
    return client_metadata_schema.metadata_schema if client_metadata_schema else None
