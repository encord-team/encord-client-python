from encord.user_client import EncordUserClient
from encord.project_ontology.ontology import Ontology

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project_client = user_client.get_project_client(
    "<project_hash>"
)

ontology: Ontology = project_client.get_project_ontology()
print(ontology.to_dict())
