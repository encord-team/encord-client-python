"""
Code Block Name: Move tasks to the next stage
"""

# Import dependencies
from encord import EncordUserClient, Project
from encord.workflow import AnnotationStage

# User input
SSH_PATH = "/Users/chris-encord/ssh-private-key.txt"
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
WORKFLOW_STAGE_NAME = "Annotate 1"
WORKFLOW_STAGE_TYPE = AnnotationStage
BUNDLE_SIZE = 100  # You can adjust this value as needed, but keep it <= 1000

# Create user client using SSH key
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Open the project you want to work on by specifying the Project ID
project = user_client.get_project(PROJECT_ID)

# Get the specific stage (in this case, "Annotate 1")
stage = project.workflow.get_stage(name=WORKFLOW_STAGE_NAME, type_=WORKFLOW_STAGE_TYPE)

# Create a bundle and move tasks
with project.create_bundle(bundle_size=BUNDLE_SIZE) as bundle:
    for task in stage.get_tasks():
        # The task is submitted as the user who is currently assigned to the task.
        # With retain_assignee=True an error occurs if there are tasks without an assignee.
        task.submit(retain_assignee=True, bundle=bundle)
        print(f"Task: {task}")

print("All tasks have been processed and moved to the next stage.")
