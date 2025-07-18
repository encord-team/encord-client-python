"""
Code Block Name: Classifications
"""

# Import dependencies
from pathlib import Path

from encord import EncordUserClient
from encord.objects import Classification, Option

SSH_PATH = "/Users/chris-encord/staging-sdk-ssh-key-private-key.txt"
# SSH_PATH = get_ssh_key() # replace it with ssh key
PROJECT_ID = "00000000-0000-0000-0000-000000000000"
BUNDLE_SIZE = 100

# Create user client
user_client: EncordUserClient = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path=SSH_PATH,
    # For US platform users use "https://api.us.encord.com"
    domain="https://api.encord.com",
)

# Get Project
project = user_client.get_project(PROJECT_ID)

# Define specific configurations for each data unit
data_unit_configs = [
    {
        "title": "anne-of-green-gables.pdf",
        "classifications": [
            {"name": "Accuracy", "type": "radio", "option": "5", "frame_range": (10, 20)},
            {"name": "Doc qualities", "type": "checklist", "options": ["Clarity", "Engaging"], "frame_range": (15, 25)},
        ],
    },
    {
        "title": "the-legend-of-sleepy-hollow.pdf",
        "classifications": [
            {"name": "Accuracy", "type": "radio", "option": "3", "frame_range": (5, 15)},
            {"name": "Edit", "type": "text", "text": "Needs more context", "frame_range": (3, 10)},
        ],
    },
    {
        "title": "the-iliad.pdf",
        "classifications": [
            {
                "name": "Doc qualities",
                "type": "checklist",
                "options": ["Logical structure", "Audience focused"],
                "frame_range": (30, 40),
            }
        ],
    },
]

# Lookup map for quicker saving later
label_row_map = {}

# Step 1: Fetch and initialize label rows in a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as init_bundle:
    for config in data_unit_configs:
        label_rows = project.list_label_rows_v2(data_title_eq=config["title"])

        assert isinstance(label_rows, list), (
            f"Expected a list of label rows for '{config['title']}', got {type(label_rows)}"
        )

        if not label_rows:
            print(f"No label row found for {config['title']}, skipping...")
            continue

        label_row = label_rows[0]
        label_row.initialise_labels(bundle=init_bundle)

        assert label_row.ontology_structure is not None, f"Ontology structure not initialized for '{config['title']}'"
        label_row_map[config["title"]] = label_row  # Save for later

# Step 2: Apply classifications
for config in data_unit_configs:
    try:
        label_row = label_row_map.get(config["title"])
        if not label_row:
            continue

        ontology_structure = label_row.ontology_structure
        assert ontology_structure is not None, f"Missing ontology structure for '{config['title']}'"

        for classification_config in config["classifications"]:
            classification = ontology_structure.get_child_by_title(
                title=classification_config["name"], type_=Classification
            )
            assert classification is not None, (
                f"Classification '{classification_config['name']}' not found in ontology for '{config['title']}'"
            )

            classification_instance = classification.create_instance()

            if classification_config["type"] == "radio":
                option = classification.get_child_by_title(title=classification_config["option"], type_=Option)
                assert option is not None, (
                    f"Radio option '{classification_config['option']}' not found in classification '{classification_config['name']}'"
                )
                classification_instance.set_answer(option)

            elif classification_config["type"] == "checklist":
                options = []
                for opt_title in classification_config["options"]:
                    option = classification.get_child_by_title(title=opt_title, type_=Option)
                    assert option is not None, (
                        f"Checklist option '{opt_title}' not found in classification '{classification_config['name']}'"
                    )
                    options.append(option)
                classification_instance.set_answer(options)

            elif classification_config["type"] == "text":
                assert "text" in classification_config, (
                    f"Missing 'text' field in text classification for '{config['title']}'"
                )
                classification_instance.set_answer(answer=classification_config["text"])

            else:
                raise ValueError(f"Unsupported classification type: {classification_config['type']}")

            start_frame, end_frame = classification_config["frame_range"]
            assert isinstance(start_frame, int) and isinstance(end_frame, int) and start_frame <= end_frame, (
                f"Invalid frame range {classification_config['frame_range']} for '{config['title']}'"
            )

            for frame in range(start_frame, end_frame + 1):
                classification_instance.set_for_frames(frames=frame, manual_annotation=True, confidence=1.0)

            label_row.add_classification_instance(classification_instance)

    except Exception as e:
        print(f"Error processing {config['title']}: {e}")

# Step 3: Save all label rows in a bundle
with project.create_bundle(bundle_size=BUNDLE_SIZE) as save_bundle:
    for label_row in label_row_map.values():
        assert label_row is not None, "Attempting to save an uninitialized label row"
        label_row.save(bundle=save_bundle)

print("All label rows processed and saved.")
