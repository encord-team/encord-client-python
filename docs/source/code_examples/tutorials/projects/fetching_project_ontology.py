from encord.client import EncordClientProject
from encord.project_ontology.ontology import Ontology
from encord.user_client import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project_client: EncordClientProject = user_client.get_project_client(
    "<project_hash>"
)

ontology: Ontology = project_client.get_project_ontology()
print(ontology.to_dict())
