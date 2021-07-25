#
# Copyright (c) 2020 Cord Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from cord.constants.model import FAST_AI, YOLOV5, FASTER_RCNN, MASK_RCNN
from cord.orm.model import ModelTrainingWeights

fast_ai = ModelTrainingWeights({
    "model": FAST_AI,
    "training_config_link": "",
    "training_weights_link": ""
})

yolov5x = ModelTrainingWeights({
    "model": YOLOV5,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Yolo/yolov5x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Yolo/yolov5x.pt"
})

yolov5s = ModelTrainingWeights({
    "model": YOLOV5,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Yolo/yolov5s.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Yolo/yolov5s.pt"
})

faster_rcnn_R_50_C4_1x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_R_50_C4_1x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_721ade.pkl"
})

faster_rcnn_R_50_DC5_1x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_R_50_DC5_1x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_51d356.pkl"
})

faster_rcnn_R_50_FPN_1x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_R_50_FPN_1x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_b275ba.pkl"
})

faster_rcnn_R_50_C4_3x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_R_50_C4_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_f97cb7.pkl"
})

faster_rcnn_R_50_DC5_3x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_R_50_DC5_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_68d202.pkl"
})

faster_rcnn_R_50_FPN_3x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_R_50_FPN_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_280758.pkl"
})

faster_rcnn_R_101_C4_3x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_R_101_C4_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_298dad.pkl"
})

faster_rcnn_R_101_DC5_3x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_R_101_DC5_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_3e0943.pkl"
})

faster_rcnn_R_101_FPN_3x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_R_101_FPN_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_f6e8b1.pkl"
})

faster_rcnn_X_101_32x8d_FPN_3x = ModelTrainingWeights({
    "model": FASTER_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/faster_rcnn_X_101_32x8d_FPN_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_68b088.pkl"
})

mask_rcnn_X_101_32x8d_FPN_3x = ModelTrainingWeights({
    "model": MASK_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/mask_rcnn_X_101_32x8d_FPN_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_2d9806.pkl"
})

mask_rcnn_R_50_C4_1x = ModelTrainingWeights({
    "model": MASK_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/mask_rcnn_R_50_C4_1x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_9243eb.pkl"
})

mask_rcnn_R_50_C4_3x = ModelTrainingWeights({
    "model": MASK_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/mask_rcnn_R_50_C4_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_4ce675.pkl"
})

mask_rcnn_R_101_FPN_3x = ModelTrainingWeights({
    "model": MASK_RCNN,
    "training_config_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/config/mask_rcnn_R_101_FPN_3x.yaml",
    "training_weights_link": "https://cord-models.s3.eu-west-2.amazonaws.com/Detectron/weights/model_final_a3ec72.pkl"
})
