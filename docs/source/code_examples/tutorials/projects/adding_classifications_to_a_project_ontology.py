from encord.client import EncordClientProject
from encord.project_ontology.classification_type import ClassificationType
from encord.user_client import EncordUserClient

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project_client: EncordClientProject = user_client.get_project_client(
    "<project_hash>"
)

success: bool = project_client.add_classification(
    "Animal",
    classification_type=ClassificationType.RADIO,
    required=True,
    options=["Cat", "Dog"],
)
print(success)
