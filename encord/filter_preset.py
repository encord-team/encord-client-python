from datetime import datetime
from typing import Iterator, List, Optional, Union
from uuid import UUID

from encord.exceptions import (
    AuthorisationError,
)
from encord.http.v2.api_client import ApiClient
from encord.orm.filter_preset import (
    CreatePresetParams,
    CreatePresetPayload,
    FilterPresetDefinition,
    GetPresetParams,
    GetPresetsResponse,
    UpdatePresetPayload,
)
from encord.orm.filter_preset import FilterPreset as OrmFilterPreset


class FilterPreset:
    """
    Represents preset in Index.
    Preset is a group of filters persisted which can be re-used for faster data curation.
    """

    def __init__(self, client: ApiClient, orm_preset: OrmFilterPreset):
        self._client = client
        self._preset_instance = orm_preset

    @property
    def uuid(self) -> UUID:
        """
        Get the preset uuid (i.e. the preset ID).

        Returns:
            str: The preset uuid.
        """
        return self._preset_instance.uuid

    @property
    def name(self) -> str:
        """
        Get the preset name

        Returns:
            str: The preset name.
        """
        return self._preset_instance.name

    @property
    def description(self) -> Optional[str]:
        """
        Get the preset description

        Returns:
            Optional[str]: The preset description.
        """
        return self._preset_instance.description

    @property
    def created_at(self) -> Optional[datetime]:
        """
        Get the preset creation timestamp

        Returns:
            Optional[datetime]: The preset creation timestamp.
        """
        return self._preset_instance.created_at

    @property
    def last_updated_at(self) -> Optional[datetime]:
        """
        Get the preset last update timestamp

        Returns:
            Optional[datetime]: The preset last update timestamp.
        """
        return self._preset_instance.last_updated_at

    @staticmethod
    def _get_preset(api_client: ApiClient, preset_uuid: UUID) -> "FilterPreset":
        params = GetPresetParams(uuids=[preset_uuid])
        orm_item = api_client.get(
            "index/presets",
            params=params,
            result_type=GetPresetsResponse,
        )
        if len(orm_item.results) > 0:
            return FilterPreset(api_client, orm_item.results[0])
        raise AuthorisationError("Collection not found")

    @staticmethod
    def _get_presets(
        api_client: ApiClient,
        preset_uuids: List[UUID],
        page_size: Optional[int] = None,
    ) -> Iterator["FilterPreset"]:
        params = GetPresetParams(uuids=preset_uuids, pageSize=page_size)
        paged_items = api_client.get_paged_iterator(
            "index/presets",
            params=params,
            result_type=OrmFilterPreset,
        )
        for item in paged_items:
            yield FilterPreset(api_client, item)

    @staticmethod
    def _list_presets(
        api_client: ApiClient, top_level_folder_uuid: Union[UUID, None], page_size: Optional[int] = None
    ) -> Iterator["FilterPreset"]:
        params = GetPresetParams(topLevelFolderUuid=top_level_folder_uuid, pageSize=page_size)
        paged_items = api_client.get_paged_iterator(
            "index/presets",
            params=params,
            result_type=OrmFilterPreset,
        )
        for item in paged_items:
            yield FilterPreset(api_client, item)

    @staticmethod
    def _delete_preset(api_client: ApiClient, preset_uuid: UUID) -> None:
        api_client.delete(
            f"index/presets/{preset_uuid}",
            params=None,
            result_type=None,
        )

    @staticmethod
    def _create_preset(api_client: ApiClient, name: str, description: str = "", *, filter_preset_json: dict) -> UUID:
        payload = CreatePresetPayload(
            name=name,
            description=description,
            filter_preset_json=FilterPresetDefinition.from_dict(filter_preset_json).to_dict(),
        )
        return api_client.post(
            "index/presets",
            payload=payload,
            params=CreatePresetParams(),
            result_type=UUID,
        )

    def get_filter_preset_json(self) -> FilterPresetDefinition:
        return self._client.get(
            f"index/presets/{self._preset_instance.uuid}",
            params=None,
            result_type=FilterPresetDefinition,
        )

    def update_preset(
        self, name: Optional[str] = None, description: Optional[str] = None, filter_preset_json: Optional[dict] = None
    ) -> None:
        """
        Update the preset's definition.
        Args:
           name (Optional[str]): The new name for the preset.
           description (Optional[str]): The new description for the preset.
           filter_preset_json (Optional[dict]): The new filters for the preset in their raw json format.
        """
        filters_definition = None
        if isinstance(filter_preset_json, dict):
            filters_definition = FilterPresetDefinition.from_dict(filter_preset_json)
        elif isinstance(filter_preset_json, FilterPresetDefinition):
            filters_definition = filter_preset_json
        payload = UpdatePresetPayload(name=name, description=description, filter_preset=filters_definition)
        __import__("pdb").set_trace()
        self._client.patch(
            f"index/presets/{self.uuid}",
            params=None,
            payload=payload,
            result_type=None,
        )
