from encord import EncordUserClient
from encord.orm.dataset import DatasetUserRole
from encord.orm.group import ProjectGroupParam, DatasetGroupParam, OntologyGroupParam
from encord.orm.ontology import OntologyUserRole
from encord.utilities.project_user import ProjectUserRole

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)


# Add Group to Project
project = user_client.get_project("<project_hash>")
groups = user_client.list_groups()
for group in groups:
    if group.name == "TestGroup":
        project.add_group(group_param=ProjectGroupParam(group_hash=group.group_hash, user_role=ProjectUserRole.ADMIN))


# Add Group to Dataset
dataset = user_client.get_dataset("<dataset_hash>")
groups = user_client.list_groups()
for group in groups:
    if group.name == "TestGroup":
        dataset.add_group(group_param=DatasetGroupParam(group_hash=group.group_hash, user_role=DatasetUserRole.ADMIN))


# Add Group to Ontologies
ontology = user_client.get_ontology("<ontology_hash>")
groups = user_client.list_groups()
for group in groups:
    if group.name == "TestGroup":
        ontology.add_group(group_param=OntologyGroupParam(group_hash=group.group_hash, user_role=OntologyUserRole.ADMIN))
