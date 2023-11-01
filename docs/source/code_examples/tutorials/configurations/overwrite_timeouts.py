from encord import EncordUserClient
from encord.http.constants import RequestsSettings

NEW_TIMEOUT = 300  # seconds

requests_settings = RequestsSettings(
    connect_timeout=NEW_TIMEOUT,
    read_timeout=NEW_TIMEOUT,
    write_timeout=NEW_TIMEOUT,
)

user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    "<your_private_key>", requests_settings=requests_settings
)
