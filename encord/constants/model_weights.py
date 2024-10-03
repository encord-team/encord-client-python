"""
---
title: "Model Weights"
slug: "sdk-ref-model-weights"
hidden: false
metadata:
  title: "Model Weights"
  description: "Encord SDK Model Weights."
category: "64e481b57b6027003f20aaa0"
---
"""

from encord.constants.model import AutomationModels
from encord.orm.model import ModelTrainingWeights

fast_ai = ModelTrainingWeights(
    {
        "model": AutomationModels.FAST_AI.value,
        "training_weights_link": None,
    }
)

faster_rcnn_R_50_C4_1x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_721ade.pkl",
    }
)

faster_rcnn_R_50_DC5_1x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_51d356.pkl",
    }
)

faster_rcnn_R_50_FPN_1x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_b275ba.pkl",
    }
)

faster_rcnn_R_50_C4_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_f97cb7.pkl",
    }
)

faster_rcnn_R_50_DC5_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_68d202.pkl",
    }
)

faster_rcnn_R_50_FPN_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_280758.pkl",
    }
)

faster_rcnn_R_101_C4_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_298dad.pkl",
    }
)

faster_rcnn_R_101_DC5_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_3e0943.pkl",
    }
)

faster_rcnn_R_101_FPN_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_f6e8b1.pkl",
    }
)

faster_rcnn_X_101_32x8d_FPN_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.FASTER_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_68b088.pkl",
    }
)

mask_rcnn_X_101_32x8d_FPN_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.MASK_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_2d9806.pkl",
    }
)

mask_rcnn_R_50_C4_1x = ModelTrainingWeights(
    {
        "model": AutomationModels.MASK_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_9243eb.pkl",
    }
)

mask_rcnn_R_50_C4_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.MASK_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_4ce675.pkl",
    }
)

mask_rcnn_R_101_FPN_3x = ModelTrainingWeights(
    {
        "model": AutomationModels.MASK_RCNN.value,
        "training_weights_link": "https://storage.googleapis.com/aws_model_backup/model_final_a3ec72.pkl",
    }
)
