import datetime
from typing import Optional

from encord.configs import SshConfig
from encord.http.querier import Querier
from encord.objects.ontology_labels_impl import Ontology as OrmOntology
from encord.objects.ontology_labels_impl import OntologyStructure


class Ontology:
    """
    Access ontology related data and manipulate the ontology. Instantiate this class via
    :meth:`encord.user_client.EncordUserClient.get_ontology()`
    """

    def __init__(self, querier: Querier, config: SshConfig, instance: Optional[OrmOntology] = None):
        self._querier = querier
        self._config = config
        self._ontology_instance: Optional[OrmOntology] = instance

    @property
    def ontology_hash(self) -> str:
        """
        Get the ontology hash (i.e. the Ontology ID).
        """
        ontology_instance = self._get_ontology_instance()
        return ontology_instance.ontology_hash

    @property
    def title(self) -> str:
        """
        Get the title of the ontology.
        """
        ontology_instance = self._get_ontology_instance()
        return ontology_instance.title

    @title.setter
    def title(self, value: str) -> None:
        ontology_instance = self._get_ontology_instance()
        ontology_instance.title = value

    @property
    def description(self) -> str:
        """
        Get the description of the ontology.
        """
        ontology_instance = self._get_ontology_instance()
        return ontology_instance.description

    @description.setter
    def description(self, value: str) -> None:
        ontology_instance = self._get_ontology_instance()
        ontology_instance.description = value

    @property
    def created_at(self) -> datetime.datetime:
        """
        Get the time the ontology was created at.
        """
        ontology_instance = self._get_ontology_instance()
        return ontology_instance.created_at

    @property
    def last_edited_at(self) -> datetime.datetime:
        """
        Get the time the ontology was last edited at.
        """
        ontology_instance = self._get_ontology_instance()
        return ontology_instance.last_edited_at

    @property
    def structure(self) -> OntologyStructure:
        """
        Get the structure of the ontology.
        """
        ontology_instance = self._get_ontology_instance()
        return ontology_instance.structure

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
            self._querier.basic_put(OrmOntology, self._config.resource_id, payload)

    def _get_ontology(self):
        return self._querier.basic_getter(OrmOntology, self._config.resource_id)

    def _get_ontology_instance(self):
        if self._ontology_instance is None:
            self._ontology_instance = self._get_ontology()
        return self._ontology_instance
