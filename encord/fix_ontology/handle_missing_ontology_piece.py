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

PROJECT_HASH = '3cc77552-e305-4544-a446-20427b5045ef'

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

skipped = 0
for lab_num, lr in enumerate(project.list_label_rows_v2()):
    if lr.label_hash in checked_labels:
        skipped += 1
        print(f"Skipped label hash: {lr.label_hash} - skipped: {skipped}/{len(checked_labels)}")
    else:
        print(f"Label Hash: {lr.label_hash} \n Label Number: {lab_num-skipped}/{num_labs}")
        if lr.label_hash is not None:
            # Create a StringHandler instance and add it to the root logger
            handler = StringHandler()
            logging.getLogger().addHandler(handler)

            lr_v1 = project.get_label_row(lr.label_hash)

            print('V1 Captured warnings:', handler.log_messages)

            # initialise labels
            lr.initialise_labels()
            lr_dict = lr.to_encord_dict()

            # print('V2 Captured warnings:', handler.log_messages)
            if len(handler.log_messages) > 0:
                # save a backup copy of labels
                with open(f"{PROJECT_HASH}/{lr.label_hash}_bkp.json", "w") as f:
                    json.dump(lr_v1, f)
                print("SAVING JSON:", f"{lr.label_hash}_bkp.json")
                # save a backup of the label row
                with open(f"{PROJECT_HASH}/{lr.label_hash}_edit.json", "w") as f:
                    json.dump(lr_dict, f)
                print("SAVING JSON:", f"{lr.label_hash}_edit.json")

                lr.save()
                print("Saved LRV2")

                label_hashes["Label Hash"].append(lr.label_hash)
                label_hashes["Status"].append(handler.log_messages)
            else:
                label_hashes["Label Hash"].append(lr.label_hash)
                label_hashes["Status"].append(handler.log_messages)
        else:
            print("Skipping")
            lr.initialise_labels()
            label_hashes["Label Hash"].append(lr.label_hash)
            label_hashes["Status"].append(["Skipping"])
        label_hashes_df = pd.DataFrame(label_hashes)
        label_hashes_df.to_csv(PROJECT_HASH + "_label_hashes.csv", index=False)