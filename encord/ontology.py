import datetime
from typing import Iterable
from uuid import UUID

from encord.group import Group
from encord.http.querier import Querier
from encord.http.v2.api_client import ApiClient
from encord.http.v2.payloads import Page
from encord.objects.ontology_structure import OntologyStructure
from encord.orm.group import Group as OrmGroup
from encord.orm.group import OntologyGroupParam
from encord.orm.ontology import Ontology as OrmOntology


class Ontology:
    """
    Access ontology related data and manipulate the ontology. Instantiate this class via
    :meth:`encord.user_client.EncordUserClient.get_ontology()`
    """

    def __init__(self, querier: Querier, instance: OrmOntology, api_client: ApiClient):
        self._querier = querier
        self._ontology_instance = instance
        self.api_client = api_client

    @property
    def ontology_hash(self) -> str:
        """
        Get the ontology hash (i.e. the Ontology ID).
        """
        return self._ontology_instance.ontology_hash

    @property
    def title(self) -> str:
        """
        Get the title of the ontology.
        """
        return self._ontology_instance.title

    @title.setter
    def title(self, value: str) -> None:
        self._ontology_instance.title = value

    @property
    def description(self) -> str:
        """
        Get the description of the ontology.
        """
        return self._ontology_instance.description

    @description.setter
    def description(self, value: str) -> None:
        self._ontology_instance.description = value

    @property
    def created_at(self) -> datetime.datetime:
        """
        Get the time the ontology was created at.
        """
        return self._ontology_instance.created_at

    @property
    def last_edited_at(self) -> datetime.datetime:
        """
        Get the time the ontology was last edited at.
        """
        return self._ontology_instance.last_edited_at

    @property
    def structure(self) -> OntologyStructure:
        """
        Get the structure of the ontology.
        """
        return self._ontology_instance.structure

    def refetch_data(self) -> None:
        """
        The Ontology class will only fetch its properties once. Use this function if you suspect the state of those
        properties to be dirty.
        """
        self._ontology_instance = self._get_ontology()

    def save(self) -> None:
        """
        Sync local state to the server, if updates are made to structure, title or description fields
        """
        if self._ontology_instance:
            payload = dict(**self._ontology_instance)
            payload["editor"] = self._ontology_instance.structure.to_dict()  # we're using internal/legacy name here
            payload.pop("structure", None)
            self._querier.basic_put(OrmOntology, self._ontology_instance.ontology_hash, payload)

    def _get_ontology(self):
        return self._querier.basic_getter(OrmOntology, self._ontology_instance.ontology_hash)

    def list_groups(self) -> Iterable[OrmGroup]:
        """
        List all groups that have access to a particular ontology
        """
        while True:
            page = self.api_client.get(
                f"ontologies/{self.ontology_hash}/group", params=None, result_type=Page[OrmGroup]
            )

            yield from page.results

            break

    def add_group(self, group_param: OntologyGroupParam):
        """
        Add group to an ontology

        Args:
            group_param: Object containing (1) hash of the group to be added and (2) user role that the group will be given

        Returns:
            Iterable of updated groups associated with the ontology
        """
        self.api_client.post(
            f"ontologies/{self.ontology_hash}/group", params=None, payload=group_param, result_type=Page[OrmGroup]
        )

    def remove_group(self, group_hash: UUID):
        """
        Remove group from ontology

        Args:
            group_hash: hash of the group to be removed

        Returns:
            Iterable of updated groups associated with the ontology
        """
        while True:
            page = self.api_client.delete(
                f"ontologies/{self.ontology_hash}/group/{group_hash}", params=None, result_type=Page[OrmGroup]
            )
            yield from page.results

            break