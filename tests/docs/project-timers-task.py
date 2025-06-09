"""
Code Block Name: View Project details
"""

from datetime import datetime, timedelta
from encord import EncordUserClient
from collections import defaultdict


# --- Configuration ---
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt" # Replace with the file path to your SSH key
PROJECT_ID = "60548e3f-4877-4bde-be08-95b5965572f6" # Replace with the project unique ID

# --- Connect to Encord ---
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

project = user_client.get_project(PROJECT_ID)

# --- Get Time Entries ---
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 6, 8)

# Returns all data
time_entries = list(project.list_time_spent(start=start_date, end=end_date))

# Filters for task time

task_time = defaultdict(int)
for entry in time_entries:
    task_time[str(entry.workflow_task_uuid)] += entry.time_spent_seconds

for task, seconds in sorted(task_time.items(), key=lambda x: x[1], reverse=True):
    print(f"Task UUID: {task} | {seconds:>5} sec | {seconds / 60:>5.1f} min")
