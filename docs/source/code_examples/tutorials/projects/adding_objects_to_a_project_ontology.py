from encord.project_ontology.object_type import ObjectShape
from encord.user_client import EncordUserClient

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project_client = user_client.get_project_client(
    "<project_hash>"
)

project_client.add_object("Dog", ObjectShape.BOUNDING_BOX)
