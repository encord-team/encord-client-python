"""---
title: "Ontology"
slug: "sdk-ref-ontology"
hidden: false
metadata:
  title: "Ontology"
  description: "Encord SDK Ontology class"
category: "64e481b57b6027003f20aaa0"
---
"""

import datetime
from typing import Iterable, List, Optional, Union
from uuid import UUID

from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.objects.ontology_structure import OntologyStructure
from encord.orm.group import AddOntologyGroupsPayload, OntologyGroup, RemoveGroupsParams
from encord.orm.ontology import CreateOrUpdateOntologyPayload
from encord.orm.ontology import Ontology as OrmOntology
from encord.utilities.hash_utilities import convert_to_uuid
from encord.utilities.ontology_user import OntologyUserRole, OntologyWithUserRole


class Ontology:
    """Access ontology related data and manipulate the ontology. Instantiate this class via
    :meth:`encord.user_client.EncordUserClient.get_ontology()`
    """

    def __init__(self, instance: Union[OrmOntology], api_client: ApiClient):
        self._ontology_instance = instance
        self.api_client = api_client

    @property
    def ontology_hash(self) -> str:
        """Get the ontology hash (i.e. the Ontology ID)."""
        return self._ontology_instance.ontology_hash

    @property
    def title(self) -> str:
        """Get the title of the ontology."""
        return self._ontology_instance.title

    @title.setter
    def title(self, value: str) -> None:
        self._ontology_instance.title = value

    @property
    def description(self) -> str:
        """Get the description of the ontology."""
        return self._ontology_instance.description

    @description.setter
    def description(self, value: str) -> None:
        self._ontology_instance.description = value

    @property
    def created_at(self) -> datetime.datetime:
        """Get the time the ontology was created at."""
        return self._ontology_instance.created_at

    @property
    def last_edited_at(self) -> datetime.datetime:
        """Get the time the ontology was last edited at."""
        return self._ontology_instance.last_edited_at

    @property
    def structure(self) -> OntologyStructure:
        """Get the structure of the ontology."""
        return self._ontology_instance.structure

    @property
    def user_role(self) -> Optional[OntologyUserRole]:
        return self._ontology_instance.user_role

    def refetch_data(self) -> None:
        """The Ontology class will only fetch its properties once. Use this function if you suspect the state of those
        properties to be dirty.
        """
        cls = type(self)
        self._ontology_instance = cls._fetch_ontology(self.api_client, self.ontology_hash)

    def save(self) -> None:
        """Sync local state to the server, if updates are made to structure, title or description fields"""
        if self._ontology_instance:
            try:
                structure_dict = self._ontology_instance.structure.to_dict()
            except ValueError as e:
                raise ValueError("Can't save an Ontology containing a Classification without any attributes. " + str(e))

            payload = CreateOrUpdateOntologyPayload(
                title=self.title,
                description=self.description,
                editor=structure_dict,
            )

            self.api_client.put(
                f"ontologies/{self._ontology_instance.ontology_hash}",
                params=None,
                payload=payload,
            )

    def list_groups(self) -> Iterable[OntologyGroup]:
        """List all groups that have access to a particular ontology."""
        ontology_hash = convert_to_uuid(self.ontology_hash)
        page = self.api_client.get(f"ontologies/{ontology_hash}/groups", params=None, result_type=Page[OntologyGroup])

        yield from page.results

    def add_group(self, group_hash: Union[List[UUID], UUID], user_role: OntologyUserRole):
        """Add group to an ontology.

        Args:
            group_hash: List of group hashes to be added.
            user_role: User role that the group will be given.

        Returns:
            None
        """
        ontology_hash = convert_to_uuid(self.ontology_hash)
        if isinstance(group_hash, UUID):
            group_hash = [group_hash]
        payload = AddOntologyGroupsPayload(group_hash_list=group_hash, user_role=user_role)
        self.api_client.post(
            f"ontologies/{ontology_hash}/groups",
            params=None,
            payload=payload,
            result_type=None,
        )

    def remove_group(self, group_hash: Union[List[UUID], UUID]):
        """Remove group from ontology.

        Args:
            group_hash: List of group hashes to be removed.

        Returns:
            None
        """
        ontology_hash = convert_to_uuid(self.ontology_hash)
        if isinstance(group_hash, UUID):
            group_hash = [group_hash]
        params = RemoveGroupsParams(group_hash_list=group_hash)
        self.api_client.delete(f"ontologies/{ontology_hash}/groups", params=params, result_type=None)

    @staticmethod
    def _legacy_orm_from_api_payload(
        ontology_with_user_role: OntologyWithUserRole,
    ) -> OrmOntology:
        flattened = ontology_with_user_role.to_dict(
            by_alias=False,  # we need 'python' names for the legacy ORM
        )
        flattened["ontology_hash"] = flattened.pop("ontology_uuid")  # backwards compat
        return OrmOntology.from_dict(flattened)

    @staticmethod
    def _from_api_payload(
        ontology_with_user_role: OntologyWithUserRole,
        api_client: ApiClient,
    ) -> "Ontology":
        return Ontology(
            Ontology._legacy_orm_from_api_payload(ontology_with_user_role),
            api_client,
        )

    @classmethod
    def _fetch_ontology(cls, api_client: ApiClient, ontology_hash: str) -> OrmOntology:
        ontology_model = api_client.get(
            f"/ontologies/{ontology_hash}",
            params=None,
            result_type=OntologyWithUserRole,
        )

        return cls._legacy_orm_from_api_payload(ontology_model)
