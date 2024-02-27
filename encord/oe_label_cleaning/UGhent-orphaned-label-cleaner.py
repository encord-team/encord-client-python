import json
from pprint import pprint

from encord import EncordUserClient

# set the ranges for the classifications you want to keep
TRUE_LABEL_RANGES = [[19280, 19580], [22248, 22548]]

# Connect to encord
keyfile = "/Users/encord/oe-public-key-private-key.txt"
user_client = EncordUserClient.create_with_ssh_private_key(ssh_private_key_path=keyfile)

# get the project
proj_hash = "6508ede1-cfd4-4eb7-bdc2-83508e805879"
project = user_client.get_project(proj_hash)
# get the label row for the specific data unit
data_hash = "561e8ed5-b65b-4dfb-9556-8fd73d968b43"
label_rows = project.list_label_rows_v2(data_hashes=[data_hash])
if len(label_rows) == 1:
    lr = label_rows.pop()
else:
    raise NotImplementedError("Program not built for multiple label rows")

# initialise labels, save a backup copy of labels and
lr.initialise_labels()
lr_dict = lr.to_encord_dict()
# save a backup of the label row
with open(f"{lr.label_hash}_bkp.json", "w") as f:
    json.dump(lr_dict, f)

# get the labels-by-frame dictionary
lab_row_data_unit = list(lr_dict["data_units"].keys())[0]
labels_by_frame = lr_dict["data_units"][lab_row_data_unit]["labels"]

# iterate through frame numbers
for frame_num in labels_by_frame.keys():
    # is the frame number NOT within one of our desired frame ranges
    in_true_label_range = True
    for tlr in TRUE_LABEL_RANGES:
        in_true_label_range = in_true_label_range and (not (tlr[0] <= int(frame_num) <= tlr[1]))
    # look for non-desired classifications that contain a classification
    if in_true_label_range and labels_by_frame[frame_num]["classifications"] != []:
        print("REMOVING CLASSIFICATION FROM FRAME:", frame_num, labels_by_frame[frame_num]["classifications"])
        # get ALL classification instances for that frame
        bad_class_instance_list = lr.get_classification_instances(filter_frames=int(frame_num))
        # when there is one classification per frame, extract from list.
        if len(bad_class_instance_list) == 1:
            bad_class_instance = bad_class_instance_list.pop()
            bad_class_instance.remove_from_frames(int(frame_num))
        else:
            # TODO: if you have multiple classifications in a frame then you will need to filter on classification hash.
            raise NotImplementedError("Only one classification per frame is supported")

# save an backup of the label row before initialising
with open(f"{lr.label_hash}_edited.json", "w") as f:
    json.dump(lr.to_encord_dict(), f)

print(f"FINISHED LABEL FILE: {lr.label_hash}_edited.json")

# CHECK JSONs BEFORE SAVING ! ! ! ! ! ! !
# lr.save()
