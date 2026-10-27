from datetime import datetime
from typing import Any, Dict, Iterator, Optional, Union
from uuid import UUID

from encord.http.v2.api_client import ApiClient
from encord.orm.label_set import (
    CreateLabelSetPayload,
    CutLabelSetVersionPayload,
    LabelSelectionMode,
    LabelSetOrigin,
    LabelSetSummary,
    LabelSetVersion,
    LabelSetVersionMember,
    ListLabelSetsParams,
    ListLabelSetVersionsParams,
    UpdateLabelSetPayload,
)
from encord.orm.label_set import LabelSet as OrmLabelSet


class LabelSet:
    """A label set captures the labels of a project's main branch into versions.

    Each version is a frozen record of which label rows existed at the cut, and at which revision.
    The label set's selection decides which labels each cut captures.
    """

    def __init__(self, client: ApiClient, orm_label_set: Union[OrmLabelSet, LabelSetSummary]):
        self._client = client
        self._label_set_instance = orm_label_set

    @property
    def uuid(self) -> UUID:
        """Get the label set unique identifier (UUID).

        Returns:
            UUID: The label set UUID.
        """
        return self._label_set_instance.uuid

    @property
    def project_hash(self) -> UUID:
        """Get the hash of the project whose main branch feeds the label set.

        Returns:
            UUID: The project hash.
        """
        return self._label_set_instance.project_hash

    @property
    def branch_name(self) -> str:
        """Get the name of the branch the labels are read from.

        Returns:
            str: The branch name.
        """
        return self._label_set_instance.branch_name

    @property
    def name(self) -> str:
        """Get the label set name.

        Returns:
            str: The label set name.
        """
        return self._label_set_instance.name

    @property
    def description(self) -> str:
        """Get the label set description.

        Returns:
            str: The label set description.
        """
        return self._label_set_instance.description

    @property
    def origin(self) -> LabelSetOrigin:
        """Get how the label set came to exist.

        Returns:
            LabelSetOrigin: The origin.
        """
        return self._label_set_instance.origin

    @property
    def trigger(self) -> Dict[str, Any]:
        """Get the cut trigger as the server returned it.

        The SDK does not interpret the trigger and only ever sends it back unchanged.

        Returns:
            Dict[str, Any]: The trigger.
        """
        return self._label_set_instance.trigger

    @property
    def created_by(self) -> str:
        """Get the hash of the user who created the label set.

        Returns:
            str: The user hash.
        """
        return self._label_set_instance.created_by

    @property
    def created_at(self) -> datetime:
        """Get the label set creation timestamp.

        Returns:
            datetime: When the label set was created.
        """
        return self._label_set_instance.created_at

    @property
    def label_selection_mode(self) -> Optional[LabelSelectionMode]:
        """Get which labels each cut captures.

        Returns:
            Optional[LabelSelectionMode]: The selection, or ``None`` if every label on the project's
            main branch is captured.
        """
        return self._full_instance().label_selection_mode

    def _full_instance(self) -> OrmLabelSet:
        # The list endpoint omits the selection, so a listed set is fetched in full on first need.
        if not isinstance(self._label_set_instance, OrmLabelSet):
            self._label_set_instance = self._fetch(self._client, self.uuid)
        return self._label_set_instance

    @staticmethod
    def _fetch(api_client: ApiClient, label_set_uuid: UUID) -> OrmLabelSet:
        return api_client.get(f"label-sets/{label_set_uuid}", params=None, result_type=OrmLabelSet)

    @staticmethod
    def _get_label_set(api_client: ApiClient, label_set_uuid: UUID) -> "LabelSet":
        return LabelSet(api_client, LabelSet._fetch(api_client, label_set_uuid))

    @staticmethod
    def _list_label_sets(
        api_client: ApiClient,
        project_hash: Optional[UUID],
        page_size: Optional[int] = None,
    ) -> Iterator["LabelSet"]:
        params = ListLabelSetsParams(project_hash=project_hash, limit=page_size)
        paged_items = api_client.get_items_paged_iterator(
            "label-sets",
            params=params,
            result_type=LabelSetSummary,
        )
        for item in paged_items:
            yield LabelSet(api_client, item)

    @staticmethod
    def _create_label_set(
        api_client: ApiClient,
        project_hash: UUID,
        name: str,
        description: str = "",
        label_selection_mode: Optional[LabelSelectionMode] = None,
    ) -> "LabelSet":
        payload = CreateLabelSetPayload(
            project_hash=project_hash,
            name=name,
            description=description,
            label_selection_mode=label_selection_mode,
        )
        orm_item = api_client.post(
            "label-sets",
            params=None,
            payload=payload,
            result_type=OrmLabelSet,
            allow_retries=False,
        )
        return LabelSet(api_client, orm_item)

    def update(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """Update the label set's name and/or description.

        The server replaces the whole configuration on every update, so the current selection and
        trigger are sent back unchanged.

        Args:
            name (Optional[str]): The new name for the label set. ``None`` leaves it unchanged.
            description (Optional[str]): The new description for the label set. ``None`` leaves it unchanged.
        """
        current = self._full_instance()
        self._put(
            name=current.name if name is None else name,
            description=current.description if description is None else description,
            label_selection_mode=current.label_selection_mode,
        )

    def set_label_selection_mode(self, label_selection_mode: Optional[LabelSelectionMode]) -> None:
        """Replace which labels each cut captures.

        Versions already cut are not affected.

        Args:
            label_selection_mode (Optional[LabelSelectionMode]): The new selection. ``None`` captures every
                label on the project's main branch.
        """
        current = self._full_instance()
        self._put(
            name=current.name,
            description=current.description,
            label_selection_mode=label_selection_mode,
        )

    def _put(self, name: str, description: str, label_selection_mode: Optional[LabelSelectionMode]) -> None:
        payload = UpdateLabelSetPayload(
            name=name,
            description=description,
            trigger=self._full_instance().trigger,
            label_selection_mode=label_selection_mode,
        )
        self._label_set_instance = self._client.put(
            f"label-sets/{self.uuid}",
            params=None,
            payload=payload,
            result_type=OrmLabelSet,
        )

    def cut_version(self, name: Optional[str] = None) -> LabelSetVersion:
        """Cut a new version, capturing the labels the selection currently matches.

        The call returns once the capture has finished.

        Args:
            name (Optional[str]): Name for the version. ``None`` means ``v{version_number}``.

        Returns:
            LabelSetVersion: The new version.
        """
        return self._client.post(
            f"label-sets/{self.uuid}/versions",
            params=None,
            payload=CutLabelSetVersionPayload(name=name),
            result_type=LabelSetVersion,
            allow_retries=False,
        )

    def list_versions(self, page_size: Optional[int] = None) -> Iterator[LabelSetVersion]:
        """List the versions cut from the label set.

        Args:
            page_size (Optional[int]): The number of versions to fetch per page, 1 to 100. Default is 100.

        Returns:
            Iterator[LabelSetVersion]: The versions.
        """
        params = ListLabelSetVersionsParams(limit=page_size)
        return self._client.get_items_paged_iterator(
            f"label-sets/{self.uuid}/versions",
            params=params,
            result_type=LabelSetVersion,
        )

    def get_version(self, version_uuid: Union[str, UUID]) -> LabelSetVersion:
        """Get a version of the label set by its unique identifier (UUID).

        Args:
            version_uuid (Union[str, UUID]): The version UUID.

        Returns:
            LabelSetVersion: The version.

        Raises:
            ValueError: If `version_uuid` is a badly formed UUID.
        """
        if isinstance(version_uuid, str):
            version_uuid = UUID(version_uuid)
        return self._client.get(
            f"label-sets/{self.uuid}/versions/{version_uuid}",
            params=None,
            result_type=LabelSetVersion,
        )

    def list_version_members(
        self, version: Union[LabelSetVersion, str, UUID], page_size: Optional[int] = None
    ) -> Iterator[LabelSetVersionMember]:
        """List the label rows a version captured, in label hash order.

        Args:
            version (Union[LabelSetVersion, str, UUID]): The version or its UUID.
            page_size (Optional[int]): The number of members to fetch per page, 1 to 100. Default is 100.

        Returns:
            Iterator[LabelSetVersionMember]: The captured label rows.

        Raises:
            ValueError: If `version` is a badly formed UUID.
        """
        if isinstance(version, LabelSetVersion):
            version_uuid = version.uuid
        elif isinstance(version, str):
            version_uuid = UUID(version)
        else:
            version_uuid = version
        params = ListLabelSetVersionsParams(limit=page_size)
        return self._client.get_items_paged_iterator(
            f"label-sets/{self.uuid}/versions/{version_uuid}/members",
            params=params,
            result_type=LabelSetVersionMember,
        )
