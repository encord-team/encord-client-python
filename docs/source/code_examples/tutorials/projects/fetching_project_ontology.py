from encord import EncordUserClient, Project
from encord.project_ontology.ontology import Ontology

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project: Project = user_client.get_project("<project_hash>")


ontology: Ontology = project.get_project_ontology()
print(ontology.to_dict())
