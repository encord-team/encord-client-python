"""
Code Block Name: View label logs
"""

# Import dependencies
from encord import EncordUserClient

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "f7890e41-6de8-4e66-be06-9fbe182df457"
DATA_UNIT_ID = "1041da61-d63c-4489-9001-4a56fe37f1f3"  # The unique identifier (data_hash) for the data unit


# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Check if the method get_label_logs exists in project
if hasattr(project, "get_label_logs"):
    try:
        # Fetch the logs for the given DATA_UNIT_ID
        logs = project.get_label_logs(data_hash=DATA_UNIT_ID)

        # Check if logs were returned
        if logs:
            for log in logs:
                print(log)
                break  # print the first log only
        else:
            print("No logs found for this data unit.")
    except Exception as e:
        print(f"An error occurred while fetching logs: {e}")
else:
    print("The project does not have a method to fetch label logs.")
