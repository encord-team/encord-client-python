import datetime
from typing import Dict, Optional

from encord.configs import BearerConfig, SshConfig
from encord.exceptions import EncordException
from encord.http.querier import Querier
from encord.http.v2.api_client import ApiClient
from encord.objects.ontology_structure import OntologyStructure
from encord.objects.skeleton_template import SkeletonTemplate
from encord.orm.ontology import Ontology as OrmOntology
from encord.orm.skeleton_template import SkeletonTemplateORM, SkeletonTemplatesORM


class Ontology:
    """
    Access ontology related data and manipulate the ontology. Instantiate this class via
    :meth:`encord.user_client.EncordUserClient.get_ontology()`
    """

    def __init__(self, querier: Querier, instance: OrmOntology, api_client: Optional[ApiClient] = None):
        self._querier = querier
        self._ontology_instance = instance
        self._api_client = api_client
        self._skeleton_templates = self._get_skeleton_templates()

    def _get_api_client(self) -> ApiClient:
        if not self._api_client:
            raise EncordException(
                "This functionality requires private SSH key authentication. API keys are not supported."
            )

        return self._api_client

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

    def _get_skeleton_templates(self) -> Dict[str, SkeletonTemplate]:
        try:
            api_client = self._get_api_client()
        except EncordException:
            return {}
        orm_templates = (
            api_client
            .get(f"/ontologies/{self.ontology_hash}/skeleton-templates", params=None, result_type=SkeletonTemplatesORM)
            .templates
        )
        skeleton_templates = [SkeletonTemplate.from_dict(orm_template.template) for orm_template in orm_templates]
        return {template.name: template for template in skeleton_templates}
