******
Models
******

.. note::
    This page is undergoing a reconstruction [Monday, May 9th 2022].

The Python SDK allows you to interact with the Encord model features.
Our model library includes state-of-the-art classification, object detection, segmentation, and pose estimation models.

Creating a model row
====================

The easiest way to get started with creating a model row is to navigate to the 'models' tab in your project. Create a model and set parameters accordingly.

.. figure:: /images/python_sdk_model_create.png

    Getting model API details.

Click on the 'Model API details' button to toggle a code snippet with create model row API details when you are happy with your selected parameters.

.. code-block::

    from encord.client import EncordClient
    from encord.constants.model import *

    # Initialize project client
    client = EncordClient.initialise(
      "<project_id>",  # Project ID
      "<project_api_key>"  # API key
    )

    model_row_uid = client.create_model_row(
                                title='Sample title',
                                description='Sample description',  # Optional
                                features=['feature_uid_1', 'feature_uid_2', ...], #  List of feature feature uid's (hashes) to be included in the model.
                                model=FASTER_RCNN
                            )
    print(model_row_uid)


The following models are available, and are all imported using ``from encord.constants.model import *``.

.. code-block::

    # Classification
    FAST_AI = "fast_ai"
    RESNET18 = "resnet18"
    RESNET34 = "resnet34"
    RESNET50 = "resnet50"
    RESNET101 = "resnet101"
    RESNET152 = "resnet152"
    VGG16 = "vgg16"
    VGG19 = "vgg19"

    # Object detection
    YOLOV5 = "yolov5"
    FASTER_RCNN = "faster_rcnn"

    # Instance segmentation
    MASK_RCNN = "mask_rcnn"


Training
========

Navigate to the 'models' tab in your project to get started with model training.
Start by creating a model row using the Python SDK or by following the :xref:`create_model_guidelines`.
You can also use an existing model by clicking on the 'train' button.

Navigate through the training flow and set parameters accordingly.

.. figure:: /images/python_sdk_model_train.png

    API details for training a model.

Click on the 'Training API details' button to toggle a code snippet with model training API details when you are happy with your selected label rows and parameters.


.. code-block::

    from encord.client import EncordClient
    from encord.constants.model_weights import *

    # Initialize project client
    client = EncordClient.initialise(
      "<project_id>",  # Project ID
      "<project_api_key>"  # API key with model.train access
    )

    # Run training and print resulting model iteration object
    model_iteration = client.model_train(
      <model_uid>,
      label_rows=['label_row_uid_1', 'label_row_uid_2', ...], # Label row uid's
      epochs=500, # Number of passes through training dataset.
      batch_size=24, # Number of training examples utilized in one iteration.
      weights=fast_ai, # Model weights.
      device="cuda" # Device (CPU or CUDA/GPU, default is CUDA).
    )
    print(model_iteration)


It is important that the weights used for the model training is compatible with the created model.
For example, if you have created a ``faster_rcnn`` object detection model, you should use ``faster_rcnn`` weights.

The following pre-trained weights are available for training, and are all imported using ``from encord.constants.model_weights import *``.

.. code-block::

    # Fast AI (classification)
    fast_ai

    # Yolo V5 (object detection)
    yolov5x
    yolov5s

    # Faster RCNN (object detection)
    faster_rcnn_R_50_C4_1x
    faster_rcnn_R_50_DC5_1x
    faster_rcnn_R_50_FPN_1x
    faster_rcnn_R_50_C4_3x
    faster_rcnn_R_50_DC5_3x
    faster_rcnn_R_50_FPN_3x
    faster_rcnn_R_101_C4_3x
    faster_rcnn_R_101_DC5_3x
    faster_rcnn_R_101_FPN_3x
    faster_rcnn_X_101_32x8d_FPN_3x

    # Mask RCNN (instance segmentation)
    mask_rcnn_X_101_32x8d_FPN_3x
    mask_rcnn_R_50_C4_1x
    mask_rcnn_R_50_C4_3x
    mask_rcnn_R_101_FPN_3x


Inference
=========

To get started with model inference, make sure you have created a project API key with ``model.inference`` added to access scopes.
The easiest way to get started with model inference is to navigate to the 'models' tab in your project.

Open the model training log for the model you would like to use for inference.

.. figure:: /images/python_sdk_model_inference.png

    API details for running inference.

Click the 'inference API details' icon next to the download button to toggle a code snippet with model inference details.

.. code-block::

    from encord.client import EncordClient

    # Initialize project client
    client = EncordClient.initialise(
      "<project_id>",  # Project ID
      "<project_api_key>"  # API key with model.inference access
    )

    # Run inference and print inference result
    inference_result = client.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      data_hashes=['video1_data_hash', 'video2_data_hash'],  # List of data_hash values for videos/image groups
      detection_frame_range=[0, 100],  # Run detection on frames 0 to 100
    )
    print(inference_result)


You can run inference on existing videos/image groups in the platform.
You can do the same by specifying the ``data_hashes`` parameter which is the list of unique identifiers of the video/image groups on which you want to run inference.
You can define confidence, intersection-over-union (IoU) and polygon coarseness thresholds.
The default confidence threshold is set to ``0.6``, the default IoU threshold is set to ``0.3`` and the default value for the polygon coarseness is set to ``0.005``.


.. code-block::

    inference_result = client.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      data_hashes=['video1_data_hash', 'video2_data_hash'],  # List of data_hash values for videos/image groups
      detection_frame_range=[0, 100],  # Run detection on frames 0 to 100
      conf_thresh=0.6,  # Set confidence threshold to 0.6
      iou_thresh=0.3,  # Set IoU threshold to 0.3
      rdp_thresh=0.005,  # Set polygon coarseness to 0.005
    )
    print(inference_result)


The model inference API also accepts a list of locally stored images to run inference on.
In case of locally stored images only JPEG and PNG file types are supported for running inference.

.. code-block::

    inference_result = client.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      file_paths=['path/to/file/1.jpg', 'path/to/file/2.jpg'],  # Local file paths to images
      detection_frame_range=[1,1],
    )
    print(inference_result)

For running inference on locally stored videos, only MP4 and WebM video types are supported.


.. code-block::

    inference_result = client.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      file_paths=['path/to/file/1.mp4', 'path/to/file/2.mp4'],  # Local file paths to videos
      detection_frame_range=[0, 100],  # Run detection on frames 0 to 100
    )
    print(inference_result)


The model inference API also accepts a list of base64 encoded strings.

.. code-block::

    inference_result = client.model_inference(
      "<model_iteration_id>",  # Model iteration ID
      base64_strings=[base64_str_1, base_64_str_2],  # Base 64 encoded strings of images/videos
      detection_frame_range=[1,1],
    )
    print(inference_result)

Limits on the input values
* ``conf_thresh`` - the value of this parameter should be between 0 and 1.
* ``iou_thresh`` - the value of this parameter should be between 0 and 1.
* ``rdp_thresh`` - the value for this paramater should be between 0 and 0.01.
* ``data_hashes`` - the cumulative size of the videos/image groups specified should be less than or equal to 1 GB, otherwise a FileSizeNotSupportedError would be thrown.
* ``detection_frame_range`` - the maximum difference between the 2 frame range values can be 1000, otherwise a DetectionRangeInvalidError would be thrown.

