from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import List, Optional, Union, cast
from uuid import UUID

import encord.orm.storage
from encord import EncordUserClient
from encord.http.bundle import BundlablePayload, Bundle, bundled_operation
from encord.http.v2.api_client import ApiClient
from encord.orm.base_dto import BaseDTO
from encord.orm.cloud_integration import CloudIntegration
from encord.storage import StorageItem

STORAGE_CLOUD_DATA_MIGRATION_BUNDLE_LIMIT = 1000


def update_storage_item_cloud_info(
    user_client: EncordUserClient,
    item: Union[StorageItem, UUID, str],
    new_url: Optional[str] = None,
    new_cloud_integration: Optional[Union[CloudIntegration, str, UUID]] = None,
    from_cloud_integration: Optional[Union[CloudIntegration, str, UUID]] = None,
    verify_access: bool = True,
    skip_missing: bool = False,
    bundle: Optional[Bundle] = None,
) -> None:
    """
    Update the cloud storage information of a storage item. This can be used to avoid re-importing data when the cloud
    configuration changes (and thus the data is accessible through a different cloud integration), or if the data has
    been moved to a different location (and thus the URL has changed).

    :param user_client: The user client to use.
    :param item: The item to update. Can be either a StorageItem instance, the item's UUID, or the URL of the item.
    :param new_url: The new URL to set. URL will be left unchanged if `None` is passed.
    :param new_cloud_integration: The new cloud integration to set. Cloud integration will be left unchanged if `None`
        is passed.
    :param from_cloud_integration: The cloud integration to update from. Acts as a check: no update will be performed if
        cloud integration of the item does not match this value. If `None`, the check will be skipped.
    :param verify_access: Whether to verify access to the item.
    :param skip_missing: if true, no error will be raised if the item is not found. Otherwise, the operation (and
        the operations in the same bundle) will be cancelled and an error will be raised.
    :param bundle: The optional :class:`encord.http.bundle.Bundle` instance used to group updates into bulk calls.
    """
    if not bundle:
        with Bundle() as bundle:
            update_storage_item_cloud_info(
                user_client=user_client,
                item=item,
                new_url=new_url,
                new_cloud_integration=new_cloud_integration,
                from_cloud_integration=from_cloud_integration,
                verify_access=verify_access,
                skip_missing=skip_missing,
                bundle=bundle,
            )
            return

    item_uuid: Optional[UUID] = None
    item_url: Optional[str] = None
    if isinstance(item, StorageItem):
        item_uuid = item.uuid
    elif isinstance(item, UUID):
        item_uuid = item
    else:  # it's a string
        try:
            item_uuid = UUID(item)
        except ValueError:
            item_url = item

    if not item_uuid and not item_url:
        raise ValueError("item must be either a StorageItem instance, a UUID, or a URL")

    if not new_url and not new_cloud_integration:
        raise ValueError("At least one of `new_url` or `new_cloud_integration` must be provided")

    new_cloud_integration_hash: Optional[UUID] = None

    if isinstance(new_cloud_integration, CloudIntegration):
        new_cloud_integration_hash = UUID(new_cloud_integration.id)
    elif isinstance(new_cloud_integration, UUID):
        new_cloud_integration_hash = new_cloud_integration
    elif isinstance(new_cloud_integration, str):
        new_cloud_integration_hash = UUID(new_cloud_integration)  # let the exception propagate

    from_cloud_integration_hash: Optional[UUID] = None

    if isinstance(from_cloud_integration, CloudIntegration):
        from_cloud_integration_hash = UUID(from_cloud_integration.id)
    elif isinstance(from_cloud_integration, UUID):
        from_cloud_integration_hash = from_cloud_integration
    elif isinstance(from_cloud_integration, str):
        from_cloud_integration_hash = UUID(from_cloud_integration)  # let the exception propagate

    bundled_operation(
        bundle,
        operation=user_client._api_client.get_bound_operation(_migrate_items_bundle),
        payload=BundledStorageMigrationPayload(
            item_migrations=[
                MigrateSingleItemPayload(
                    item_uuid=item_uuid,
                    item_url=item_url,
                    new_url=new_url,
                    new_cloud_integration=new_cloud_integration_hash,
                    from_cloud_integration=from_cloud_integration_hash,
                    verify_access=verify_access,
                    skip_missing=skip_missing,
                ),
            ],
        ),
        limit=STORAGE_CLOUD_DATA_MIGRATION_BUNDLE_LIMIT,
    )


class MigrateSingleItemPayload(BaseDTO):
    item_uuid: Optional[UUID]
    item_url: Optional[str]
    new_url: Optional[str]
    new_cloud_integration: Optional[UUID]
    from_cloud_integration: Optional[UUID]
    verify_access: bool
    skip_missing: bool

    def payload_key(self) -> str:
        return "::".join(
            str(part)
            for part in [
                "UUID" if self.item_uuid else "URL",
                self.new_cloud_integration,
                self.from_cloud_integration,
                self.verify_access,
                self.skip_missing,
            ]
        )


@dataclass
class BundledStorageMigrationPayload:
    item_migrations: List[MigrateSingleItemPayload]

    def add(self, other: BundledStorageMigrationPayload) -> BundledStorageMigrationPayload:
        self.item_migrations.extend(other.item_migrations)
        return self


def _migrate_items_bundle(
    api_client: ApiClient,
    *,
    item_migrations: List[MigrateSingleItemPayload],
) -> None:
    for _, single_call_items in itertools.groupby(
        sorted(((p.payload_key(), p) for p in item_migrations), key=lambda pp: pp[0]),
        key=lambda pp: pp[0],
    ):
        single_call_items_list = [pp[1] for pp in single_call_items]
        if not single_call_items_list:
            continue
        if single_call_items_list[0].item_uuid:
            items_map = {cast(UUID, p.item_uuid): p.new_url for p in single_call_items_list}
            urls_map = {}
        else:
            items_map = {}
            urls_map = {cast(str, p.item_url): p.new_url for p in single_call_items_list}

        api_client.post(
            path="/storage/items/migrate-storage",
            params=None,
            payload=encord.orm.storage.StorageItemsMigratePayload(
                urls_map=urls_map,
                items_map=items_map,
                from_integration_hash=single_call_items_list[0].from_cloud_integration,
                to_integration_hash=single_call_items_list[0].new_cloud_integration,
                validate_access=single_call_items_list[0].verify_access,
                skip_missing=single_call_items_list[0].skip_missing,
            ),
            result_type=None,
        )
