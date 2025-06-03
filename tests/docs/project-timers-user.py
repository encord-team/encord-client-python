"""
Code Block Name: View Project details
"""

from datetime import datetime, timedelta
from encord import EncordUserClient

# --- Configuration ---
SSH_PATH = "/Users/laverne-encord/staging-sdk-ssh-key-private-key.txt"
PROJECT_ID = "34aa8e8e-7397-482e-97d2-d505125edd95"
DOMAIN = "https://staging.api.encord.com"
USER_EMAIL = "laverne@encord.com"  # 👈 The collaborator whose time you want to sum

# --- Connect to Encord ---
user_client = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    domain=DOMAIN,
)

project = user_client.get_project(PROJECT_ID)

# --- Get Time Entries for User ---
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 6, 2)

time_entries = list(project.list_time_spent(
    start=start_date,
    end=end_date,
    user_email=USER_EMAIL,
))

# --- Sum up total seconds ---
total_seconds = sum(entry.time_spent_seconds for entry in time_entries)
total_duration = timedelta(seconds=total_seconds)

# --- Print human-readable duration ---
hours, remainder = divmod(total_duration.total_seconds(), 3600)
minutes, seconds = divmod(remainder, 60)

print(f"Total time spent by {USER_EMAIL}: {int(hours)}h {int(minutes)}m {int(seconds)}s")
