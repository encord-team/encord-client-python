from encord.client import EncordClient, EncordConfig

config: EncordConfig = EncordConfig("<resource_id>", "<resource_api_key>")
client: EncordClient = EncordClient.initialise_with_config(config)
