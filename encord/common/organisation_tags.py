from typing import List, Optional, Union
from uuid import UUID

from encord.exceptions import ResourceNotFoundError
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.orm.project import OrganisationTag

ORGANISATION_TAGS_PATH = "organisation/organisation-tags"


def resolve_organisation_tag_names(
    api_client: ApiClient,
    tags: Optional[Union[List[str], List[OrganisationTag]]],
) -> Optional[List[str]]:
    """Normalize a tag filter to a list of validated tag names.

    Accepts either plain tag-name strings or :class:`~encord.orm.project.OrganisationTag` instances
    (as returned by ``list_organisation_tags``) and returns their names. Returns ``None`` unchanged so
    callers can pass the result straight into an optional filter field.

    Any name supplied as a plain string is validated against the organization's tags before the
    request is sent, so that an unknown name raises a clear error naming *every* offending tag,
    rather than the request failing with an opaque server-side error that does not say which name
    was wrong. :class:`~encord.orm.project.OrganisationTag` instances are assumed valid (they come
    from the API) and are not re-validated, so a filter made up only of them needs no extra request.

    Raises:
        ResourceNotFoundError: One or more string tag names do not match any organization tag. A
            single error is raised listing all unknown names, so a filter with several bad names is
            reported in one go rather than one name at a time.
    """
    if tags is None:
        return None

    names = [tag.name if isinstance(tag, OrganisationTag) else tag for tag in tags]

    # Only plain-string names need checking; OrganisationTag instances are already known-valid, and a
    # filter built entirely from them should not trigger an extra lookup.
    names_to_validate = [tag for tag in tags if isinstance(tag, str)]
    if names_to_validate:
        known_names = {
            candidate.name
            for candidate in api_client.get(
                ORGANISATION_TAGS_PATH, params=None, result_type=Page[OrganisationTag]
            ).results
        }
        # dict.fromkeys preserves order and de-duplicates, so each bad name is reported once.
        unknown_names = [name for name in dict.fromkeys(names_to_validate) if name not in known_names]
        if unknown_names:
            quoted = ", ".join(f"'{name}'" for name in unknown_names)
            noun = "tag" if len(unknown_names) == 1 else "tags"
            verb = "exists" if len(unknown_names) == 1 else "exist"
            raise ResourceNotFoundError(
                f"No organisation {noun} named {quoted} {verb} in the organisation. "
                "Use `EncordUserClient.list_organisation_tags()` to see the available tags."
            )

    return names


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
