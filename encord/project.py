import datetime
from dataclasses import dataclass
from typing import List, Optional

from encord.client import EncordClientProject
from encord.configs import Config
from encord.encord_objects.ontology import Ontology
from encord.http.querier import Querier
from encord.orm.label_row import LabelRowMetadata
from encord.orm.project import Project as OrmProject
from encord.project_ontology.ontology import Ontology as LegacyOntology


@dataclass
class ProjectDataset:
    dataset_hash: str
    title: str
    description: str

    @staticmethod
    def from_dict(d: dict) -> "ProjectDataset":
        return ProjectDataset(
            dataset_hash=d["dataset_hash"],
            title=d["title"],
            description=d["description"],
        )

    @classmethod
    def from_list(cls, l: list) -> List["ProjectDataset"]:
        ret = []
        for i in l:
            ret.append(cls.from_dict(i))
        return ret


class Project(EncordClientProject):
    def __init__(self, querier: Querier, config: Config):
        super().__init__(querier, config)
        #  DENIS: possibly keep a parsed `ProjectDataclass` here instead of parsing every time on access.
        self._project_instance: Optional[OrmProject] = None

    def _get_project_instance(self):
        if self._project_instance is None:
            self._project_instance = self.get_project()
        return self._project_instance

    @property
    def project_hash(self) -> str:
        """
        ...
        """
        project_instance = self._get_project_instance()
        return project_instance.project_hash

    @property
    def title(self) -> str:
        """
        ...
        """
        project_instance = self._get_project_instance()
        return project_instance.title

    @property
    def description(self) -> str:
        """
        ...
        """
        project_instance = self._get_project_instance()
        return project_instance.description

    @property
    def created_at(self) -> datetime.datetime:
        """
        ...
        """
        project_instance = self._get_project_instance()
        return project_instance.created_at

    @property
    def last_edited_at(self) -> datetime.datetime:
        """
        ...
        """
        project_instance = self._get_project_instance()
        return project_instance.last_edited_at

    @property
    def editor_ontology(self) -> Ontology:
        """
        ...
        """
        project_instance = self._get_project_instance()
        return Ontology.from_dict(project_instance.editor_ontology)

    @property
    def datasets(self) -> List[ProjectDataset]:
        """
        ...
        """
        project_instance = self._get_project_instance()
        return ProjectDataset.from_list(project_instance.datasets)

    @property
    def label_rows(self) -> List[LabelRowMetadata]:
        """
        ...
        """
        project_instance = self._get_project_instance()
        return LabelRowMetadata.from_list(project_instance.label_rows)

    def refetch_data(self) -> None:
        """
        The Project class will only fetch its properties once. Use this function if you suspect the state of those
        properties to be dirty.
        """
        self._project_instance = self.get_project()

    def get_project(self) -> OrmProject:
        """
        This function is exposed for convenience. You are encouraged to use the property accessors instead.
        """
        return super().get_project()

    def get_project_ontology(self) -> LegacyOntology:
        """
        This function is exposed for convenience. You are encouraged to use the editor_ontology() property accessors
        instead. The editor_ontology() property accessor returns a more complete ontology object.
        """
        return super().get_project_ontology()
