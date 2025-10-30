from datetime import datetime
from typing import Iterator, List, Optional, Union
from uuid import UUID

from encord.client import EncordClientProject
from encord.exceptions import (
    AuthorisationError,
    EncordException,
)
from encord.http.v2.api_client import ApiClient
from encord.orm.filter_preset import (
    ActiveCreatePresetPayload,
    ActiveFilterPresetDefinition,
    ActiveUpdatePresetPayload,
    CreatePresetParams,
    GetPresetParams,
    GetPresetsResponse,
    GetProjectFilterPresetParams,
    IndexCreatePresetPayload,
    IndexFilterPresetDefinition,
    IndexUpdatePresetPayload,
)
from encord.orm.filter_preset import FilterPreset as OrmFilterPreset
from encord.orm.filter_preset import ProjectFilterPreset as OrmProjectFilterPreset


class FilterPreset:
    """Represents preset in Index.
    Preset is a group of filters persisted which can be reused for faster data curation.
    """

    def __init__(self, client: ApiClient, orm_preset: OrmFilterPreset):
        self._client = client
        self._preset_instance = orm_preset

    @property
    def uuid(self) -> UUID:
        """Get the preset uuid (i.e. the preset ID).

        Returns:
            str: The preset uuid.
        """
        return self._preset_instance.uuid

    @property
    def name(self) -> str:
        """Get the preset name

        Returns:
            str: The preset name.
        """
        return self._preset_instance.name

    @property
    def description(self) -> Optional[str]:
        """Get the preset description

        Returns:
            Optional[str]: The preset description.
        """
        return self._preset_instance.description

    @property
    def created_at(self) -> Optional[datetime]:
        """Get the preset creation timestamp

        Returns:
            Optional[datetime]: The preset creation timestamp.
        """
        return self._preset_instance.created_at

    @property
    def last_updated_at(self) -> Optional[datetime]:
        """Get the preset last update timestamp

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
        raise AuthorisationError("Preset not found")

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
        filter_preset = IndexFilterPresetDefinition.from_dict(filter_preset_json)
        if not filter_preset.local_filters and not filter_preset.global_filters:
            raise EncordException("We require there to be a non-zero number of filters in a preset")
        payload = IndexCreatePresetPayload(
            name=name,
            filter_preset_json=filter_preset.to_dict(),
            description=description,
        )
        return api_client.post(
            "index/presets",
            payload=payload,
            params=CreatePresetParams(),
            result_type=UUID,
            allow_retries=False,
        )

    def get_filter_preset_json(self) -> IndexFilterPresetDefinition:
        return self._client.get(
            f"index/presets/{self._preset_instance.uuid}",
            params=None,
            result_type=IndexFilterPresetDefinition,
        )

    def update_preset(
        self, name: Optional[str] = None, description: Optional[str] = None, filter_preset_json: Optional[dict] = None
    ) -> None:
        """Update the preset's definition.

        Args:
           name (Optional[str]): The new name for the preset.
           description (Optional[str]): The new description for the preset.
           filter_preset_json (Optional[dict]): The new filters for the preset in their raw json format.
        """
        filters_definition = None
        if isinstance(filter_preset_json, dict):
            filters_definition = IndexFilterPresetDefinition.from_dict(filter_preset_json)
        elif isinstance(filter_preset_json, IndexFilterPresetDefinition):
            filters_definition = filter_preset_json
        if filters_definition:
            if not filters_definition.local_filters and not filters_definition.global_filters:
                raise EncordException("We require there to be a non-zero number of filters in a preset")
        payload = IndexUpdatePresetPayload(name=name, description=description, filter_preset=filters_definition)
        self._client.patch(
            f"index/presets/{self.uuid}",
            params=None,
            payload=payload,
            result_type=None,
        )
        self._preset_instance.name = name or self.name
        self._preset_instance.description = description or self.description


class ProjectFilterPreset:
    """Represents Active filter presets."""

    def __init__(
        self,
        project_uuid: UUID,
        client: ApiClient,
        orm_filter_preset: OrmProjectFilterPreset,
    ):
        self._project_uuid = project_uuid
        self._client = client
        self._filter_preset_instance = orm_filter_preset

    @property
    def uuid(self) -> UUID:
        """Get the filter preset unique identifier (UUID).

        Returns:
            UUID: The filter preset UUID.
        """
        return self._filter_preset_instance.preset_uuid

    @property
    def name(self) -> str:
        """Get the filter preset name.

        Returns:
            str: The collection name.
        """
        return self._filter_preset_instance.name

    @property
    def created_at(self) -> Optional[datetime]:
        """Get the filter preset creation timestamp.

        Returns:
            Optional[datetime]: The timestamp when the filter preset was created, or None if not available.
        """
        return self._filter_preset_instance.created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        """Get the filter preset last edit timestamp.

        Returns:
            Optional[datetime]: The timestamp when the filter preset was last edited, or None if not available.
        """
        return self._filter_preset_instance.updated_at

    @property
    def project_hash(self) -> UUID:
        """Get the project hash of the filter preset.

        Returns:
            UUID: The project hash of the filter preset.
        """
        return self._project_uuid

    @staticmethod
    def _get_filter_preset(
        client: ApiClient,
        project_uuid: UUID,
        filter_preset_uuid: UUID,
    ) -> "ProjectFilterPreset":
        params = GetProjectFilterPresetParams(preset_uuids=[filter_preset_uuid])
        orm_items = list(
            client.get_paged_iterator(
                f"active/{project_uuid}/presets",
                params=params,
                result_type=OrmProjectFilterPreset,
            )
        )
        if len(orm_items) > 0:
            return ProjectFilterPreset(
                project_uuid=project_uuid,
                client=client,
                orm_filter_preset=orm_items[0],
            )
        raise AuthorisationError("No Project preset found")

    @staticmethod
    def _list_filter_presets(
        client: ApiClient,
        project_uuid: UUID,
        filter_preset_uuids: Union[List[UUID], None],
        page_size: Optional[int] = None,
    ) -> Iterator["ProjectFilterPreset"]:
        params = GetProjectFilterPresetParams(preset_uuids=filter_preset_uuids, page_size=page_size)
        paged_filter_presets = client.get_paged_iterator(
            f"active/{project_uuid}/presets",
            params=params,
            result_type=OrmProjectFilterPreset,
        )
        for filter_preset in paged_filter_presets:
            yield ProjectFilterPreset(
                project_uuid=project_uuid,
                client=client,
                orm_filter_preset=filter_preset,
            )

    @staticmethod
    def _delete_filter_preset(client: ApiClient, project_uuid: UUID, filter_preset_uuid: UUID) -> None:
        client.delete(
            f"active/{project_uuid}/presets/{filter_preset_uuid}",
            params=None,
            result_type=None,
        )

    def get_filter_preset_json(self) -> ActiveFilterPresetDefinition:
        return self._client.get(
            f"active/{self._project_uuid}/presets/{self._filter_preset_instance.preset_uuid}/raw",
            params=None,
            result_type=ActiveFilterPresetDefinition,
        )

    def update_preset(
        self, name: Optional[str] = None, filter_preset: Optional[ActiveFilterPresetDefinition] = None
    ) -> None:
        if name is None and filter_preset is None:
            return
        payload = ActiveUpdatePresetPayload(name=name, filter_preset=filter_preset)
        self._client.patch(
            f"active/{self.project_hash}/presets/{self.uuid}", params=None, payload=payload, result_type=None
        )

    @staticmethod
    def _create_filter_preset(
        client: ApiClient, project_uuid: UUID, name: str, filter_preset: ActiveFilterPresetDefinition
    ) -> UUID:
        if not filter_preset.local_filters and not filter_preset.global_filters:
            raise EncordException("We require there to be a non-zero number of filters in a preset for creation")
        payload = ActiveCreatePresetPayload(name=name, filter_preset_json=filter_preset.to_dict())
        orm_resp = client.post(
            f"active/{project_uuid}/presets",
            params=None,
            payload=payload,
            result_type=UUID,
            allow_retries=False,
        )
        return orm_resp
