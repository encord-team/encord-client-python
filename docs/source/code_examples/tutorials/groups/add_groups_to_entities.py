from encord import EncordUserClient
from encord.orm.dataset import DatasetUserRole
from encord.utilities.ontology_user import OntologyUserRole
from encord.utilities.project_user import ProjectUserRole

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)


# Add Group to Project
project = user_client.get_project("<project_hash>")
groups = user_client.list_groups()
for group in groups:
    if group.name == "TestGroup":
        project.add_group(group.group_hash, ProjectUserRole.ADMIN)
        break


# Add Group to Dataset
dataset = user_client.get_dataset("<dataset_hash>")
groups = user_client.list_groups()
for group in groups:
    if group.name == "TestGroup":
        dataset.add_group(group.group_hash, DatasetUserRole.ADMIN)
        break


# Add Group to Ontologies
ontology = user_client.get_ontology("<ontology_hash>")
groups = user_client.list_groups()
for group in groups:
    if group.name == "TestGroup":
        ontology.add_group(group.group_hash, OntologyUserRole.ADMIN)
        break
