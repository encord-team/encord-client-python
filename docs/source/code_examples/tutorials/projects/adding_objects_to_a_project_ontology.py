from encord import EncordUserClient, Project
from encord.project_ontology.object_type import ObjectShape

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key("<your_private_key>")
project: Project = user_client.get_project("<project_hash>")

success: bool = project.add_object("Dog", ObjectShape.BOUNDING_BOX)
print(success)
