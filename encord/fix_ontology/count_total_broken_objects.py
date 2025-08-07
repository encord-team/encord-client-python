import os
import json
import logging
import pandas as pd

# Optional: Add a custom handler to capture warnings in a variable
class StringHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_messages = []

    def emit(self, record):
        self.log_messages.append(record.getMessage())

from encord import EncordUserClient

# EMEA
ENCORD_KEY_PATH = "/Users/encord/source/keys/encord_key.ed25519"
DOMAIN = "https://api.encord.com"

# US
# ENCORD_KEY_PATH = "/Users/encord/source/keys/encord_key_us.ed25519"
# DOMAIN = "https://api.us.encord.com"

PROJECT_HASH = '58003f9c-705c-4c3e-8e0e-0ae32c5fb160'

client = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=ENCORD_KEY_PATH,
    domain=DOMAIN
)
logging.basicConfig(level=logging.WARNING)


project = client.get_project(PROJECT_HASH)


# Create the directory if it doesn't exist
os.makedirs(PROJECT_HASH, exist_ok=True)

checked_labels = [None]
# checked_labels = pd.read_csv(proj_hash+"_label_hashes_ROUND2.csv")["Label Hash"].to_list()

num_labs = len(project.list_label_rows_v2())
print("Total number of labels", num_labs)
num_labs = len(project.list_label_rows_v2()) - len(checked_labels)
print("Number of labels to check", num_labs)
label_hashes: dict = {"Label Hash": [], "Status": []}

missing_object_or_classification_count = 0
missing_answer_count = 0

skipped = 0
for lab_num, lr in enumerate(project.list_label_rows_v2()):
    with project.create_bundle() as bundle:
        if lr.label_hash in checked_labels:
            skipped += 1
            print(f"Skipped label hash: {lr.label_hash} - skipped: {skipped}/{len(checked_labels)}")
        else:
            print(f"Label Hash: {lr.label_hash} \n Label Number: {lab_num-skipped}/{num_labs}")
            if lr.label_hash is not None:
                # Create a StringHandler instance and add it to the root logger
                handler = StringHandler()
                logging.getLogger().addHandler(handler)

                # initialise labels
                lr.initialise_labels(bundle=bundle)

    for log in handler.log_messages:
        if "MISSING_ITEM" in log:
            missing_object_or_classification_count += 1
        if "MISSING_ANSWER" in log:
            missing_answer_count += 1

print(f"Number of Missing Object & Classification Labels: {missing_object_or_classification_count}")
print(f"Number of Answers: {missing_answer_count}")