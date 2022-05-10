from encord.client import EncordClientProject
from encord.project_ontology.object_type import ObjectShape
from encord.user_client import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project_client: EncordClientProject = user_client.get_project_client(
    "<project_hash>"
)

success: bool = project_client.add_object("Dog", ObjectShape.BOUNDING_BOX)
print(success)
