import datetime

from encord import EncordUserClient, Project

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>"
)
project: Project = user_client.get_project("<project_hash>")

for timer in project.list_collaborator_timers(
    after=datetime.datetime.now(datetime.timezone.utc)
    - datetime.timedelta(weeks=1)
):
    print(f"Collaborator session: {timer}")
