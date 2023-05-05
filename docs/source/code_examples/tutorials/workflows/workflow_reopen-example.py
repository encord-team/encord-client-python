from encord import EncordUserClient, Project

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project: Project = user_client.get_project("<workflows_project_hash>")

for label_row in project.list_label_rows_v2():
    label.workflow_reopen()
