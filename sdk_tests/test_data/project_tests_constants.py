from dataclasses import dataclass
from typing import List


from cord.client import CordClientProject


@dataclass(frozen=True)
class PytestKeys:
    private_key: str
    cord_user_endpoint: str
    cord_endpoint: str
    template_client_project: CordClientProject
    template_project_feature_hashes: List[str]
    template_project_dataset_hash: str

TRAINING_BATCH_SIZE = 5
TRAINING_EPOCH_SIZE = 1
TEMPLATE_PROJECT_DEV_ID = '1c57a760-acd9-4be4-a005-c3ef37e0968e'
TEMPLATE_PROJECT_STAGING_ID = '4d0278d1-42ae-4059-bac8-35f29059f55b'
TEMPLATE_PROJECT_DEV_FEATURE_HASHES = ["6b2736fc"]
TEMPLATE_PROJECT_STAGING_DATASET_HASH = "af3f0b4e-fac3-4d15-8975-7d163c53e133"
TEMPLATE_PROJECT_DEV_DATASET_HASH = "3da4f875-f612-4f00-8927-2cb1c3d5bda7"
TEMPLATE_PROJECT_STAGING_FEATURE_HASHES = ["bfdf30a9"]

EMPTY_LABEL_ROW = {
  'label_hash': 'a0f1e997-87fa-4d65-b29d-e4798e985eeb',
  'dataset_hash': '3da4f875-f612-4f00-8927-2cb1c3d5bda7',
  'dataset_title': 'Template Dataset',
  'data_title': 'Video Of Funny Cat.mp4',
  'data_type': 'video',
  'data_units': {
    'df0a82ac-a385-4ef4-8f2a-8a4bffc63989': {
      'data_hash': 'df0a82ac-a385-4ef4-8f2a-8a4bffc63989',
      'data_title': 'Video Of Funny Cat.mp4',
      'data_link': 'https://storage.googleapis.com/cord-ai-platform.appspot.com/cord-videos-dev/1rJzWAhyzsaDJ2kOH3RiwU4bj5x1/df0a82ac-a385-4ef4-8f2a-8a4bffc63989?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=firebase-adminsdk-64w1p%40cord-ai-platform.iam.gserviceaccount.com%2F20211213%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20211213T131218Z&X-Goog-Expires=604800&X-Goog-SignedHeaders=host&X-Goog-Signature=161ae4d6e63b7103bebec6b4f1f706fb0496c754123a99b1b81c3417008393fd4c2304ccd01627ec3a6cad5e6eb2010df86809bb727bebe9fcd3f623d13c8ecd1299d11f379498d138fcaba2425db3ab20a44e2d7d6f42d25a01d9ff2ebc06b69b0fd282020476c1814d9268961a2778f223eef17eec85dec55c7d62c10036be39b016f9fe9adc9d6df8784f53275b172eeb3ed5438cd3cf8d6a507bfee5fdd3bf7f04537b22690d972e0f121633b3b29f3ff0432bd7bd5805c90fa80057e56228ac4480e555aae58e0a989dba4e8e9c517c7fe4cf8ccaaec8b48d7a8986baca442c84c19fb3cdbf89ede44cc60082ff8390bf2d16870f74dd93cbb02cd912ac',
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
