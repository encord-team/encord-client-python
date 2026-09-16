from typing import Optional, Union
from uuid import UUID

from encord.exceptions import ResourceNotFoundError
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.project import OrganisationTag

ORGANISATION_TAGS_PATH = "organisation/organisation-tags"


def resolve_organisation_tag_uuid(
    api_client: ApiClient,
    *,
    tag: Optional[OrganisationTag],
    tag_name: Optional[str],
    tag_uuid: Optional[Union[UUID, str]],
) -> UUID:
    provided = [value for value in (tag, tag_name, tag_uuid) if value is not None]
    if len(provided) != 1:
        raise ValueError("Exactly one of `tag`, `tag_name` or `tag_uuid` must be provided.")
    if tag is not None:
        if not isinstance(tag, OrganisationTag):
            raise TypeError(
                f"`tag` must be an OrganisationTag, got {type(tag).__name__}. "
                "Pass a UUID as `tag_uuid=` or a name as `tag_name=`."
            )
        return tag.uuid
    if tag_uuid is not None:
        return tag_uuid if isinstance(tag_uuid, UUID) else UUID(tag_uuid)
    tags = api_client.get(ORGANISATION_TAGS_PATH, params=None, result_type=Page[OrganisationTag]).results
    for candidate in tags:
        if candidate.name == tag_name:
            return candidate.uuid
    raise ResourceNotFoundError(f"No organisation tag named '{tag_name}' exists in the organisation.")
