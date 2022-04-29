from encord.user_client import EncordUserClient
from encord.client import EncordClientProject

user_client = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key_content>",
    password="<your_private_key_password_if_necessary>",
)

project_hash: str = next(
    (
        p["project"]["project_hash"]
        for p in user_client.get_projects()
    )
)

project_client: EncordClientProject = (
    user_client.get_project_client(project_hash)
)
label_hash: str = next(
    (
        lr["label_hash"]
        for lr in project_client.get_project().label_rows
        if lr["label_hash"] is not None
    )
)
labels: dict = project_client.get_label_row(label_hash)
print(labels)
