from dataclasses import dataclass
from typing import List

from cord.client import CordClientProject


@dataclass(frozen=True)
class PytestKeys:
    private_key: str
    cord_domain: str
    template_client_project: CordClientProject
    template_project_feature_hashes: List[str]
    template_project_dataset_hash: str
    template_project_hash: str

TRAINING_BATCH_SIZE = 5
TRAINING_EPOCH_SIZE = 1
TEMPLATE_PROJECT_DEV_ID = '1c57a760-acd9-4be4-a005-c3ef37e0968e'
TEMPLATE_PROJECT_STAGING_ID = '4d0278d1-42ae-4059-bac8-35f29059f55b'
TEMPLATE_PROJECT_DEV_FEATURE_HASHES = ["6b2736fc"]
TEMPLATE_PROJECT_STAGING_DATASET_HASH = "af3f0b4e-fac3-4d15-8975-7d163c53e133"
TEMPLATE_PROJECT_DEV_DATASET_HASH = "3da4f875-f612-4f00-8927-2cb1c3d5bda7"
TEMPLATE_PROJECT_STAGING_FEATURE_HASHES = ["bfdf30a9"]

EMPTY_LABEL_ROW = {
  'label_hash': None,
  'dataset_hash': None,
  'dataset_title': 'Template Dataset',
  'data_title': 'Video Of Funny Cat.mp4',
  'data_type': 'video',
  'data_units': {
    'UNDEFINED': {
      'data_hash': None,
      'data_title': 'Video Of Funny Cat.mp4',
      'data_link': None,
      'data_type': 'video/mp4',
      'data_fps': 59.94006,
      'width': 1920,
      'height': 1080,
      'data_sequence': 0,
      'labels': {

      }
    }
  },
  'object_answers': {

  },
  'classification_answers': {

  },
  'object_actions': {

  },
  'label_status': 'LABEL_IN_PROGRESS'
}

DUMMY_MODEL_TRAINING_RESULT = {
  'id': None,
  'model_hash': None,
  'training_hash': None,
  'project_hash': None,
  'title': 'Test model',
  'type': 'object_detection',
  'model': 'faster_rcnn',
  'framework': 'pytorch',
  'training_epochs': 1,
  'training_batch_size': 5,
  'training_final_loss': 0.0,
  'training_config_link': None,
  'training_names_link': None,
  'training_weights_link': None,
  'cord_config_link': None,
  'created_at': None,
  'training_duration': None
}
