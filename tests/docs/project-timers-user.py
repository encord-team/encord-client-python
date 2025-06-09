"""
Code Block Name: Timers - User
"""

from collections import defaultdict
from datetime import datetime

from encord import EncordUserClient

# --- Configuration ---
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"  # Replace with the file path to your SSH key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"  # Replace with the project unique ID

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

# Filters for user

user_time = defaultdict(int)
for entry in time_entries:
    user_time[entry.user_email] += entry.time_spent_seconds

for user, seconds in sorted(user_time.items(), key=lambda x: x[1], reverse=True):
    print(f"User: {user:<30} | {seconds:>5} sec | {seconds / 60:>5.1f} min")
