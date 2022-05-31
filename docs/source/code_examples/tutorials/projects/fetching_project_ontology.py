from encord import EncordUserClient, ProjectManager
from encord.project_ontology.ontology import Ontology

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project_manager: ProjectManager = user_client.get_project_manager("<project_hash>")


ontology: Ontology = project_manager.get_project_ontology()
print(ontology.to_dict())
