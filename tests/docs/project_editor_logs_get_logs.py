"""
Code Block Name: View Editor logs
"""
from datetime import datetime, timedelta
from uuid import UUID

# Import dependencies
from encord import EncordUserClient

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
DATA_UNIT_ID = "00000000-0000-0000-0000-000000000000"  # The unique identifier (data_hash) for the data unit


# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Fetch the logs of the project with mandatory start_time and end_time parameters and a maximum of 30 days range
start_time = datetime.now() - timedelta(days=29)
end_time = datetime.now()
logs_response = project.get_editor_logs(start_time=start_time, end_time=end_time)

# Check if logs were returned
if logs_response and logs_response.logs:
    for log in logs_response.logs:
        print(log)
        break  # print the first log only

# Get the next page of logs if available
if logs_response.next_page_token:
    next_page_logs_response = project.get_editor_logs(
        start_time=start_time,
        end_time=end_time,
        page_token=logs_response.next_page_token
    )
    if next_page_logs_response and next_page_logs_response.logs:
        for log in next_page_logs_response.logs:
            print(log)
            break  # print the first log of the next page only

# Do some queries with optional parameters
filtered_logs_response = project.get_editor_logs(
    start_time=start_time,
    end_time=end_time,
    limit=200,
    action="create_object",
    actor_user_email="some-email@gmail.com",
    workflow_stage_id=UUID("some-stage-id"),
    data_unit_id=UUID("some-data-unit-id")
)
