from encord import EncordUserClient
from encord.http.constants import RequestsSettings

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>",
    requests_settings=RequestsSettings(max_retries=7, backoff_factor=0.3),
)
