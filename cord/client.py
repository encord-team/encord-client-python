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

""" ``cord.client`` provides a simple Python client that allows you
to query project resources through the Cord REST API.

Here is a simple example for instantiating the client and obtaining project info:

.. test_blurb2.py code::

    from cord.client import CordClient

    client = CordClient.initialize('YourProjectID', 'YourAPIKey')
    client.get_project()

    :returns
    Project info. See Project ORM for details.

"""

import sys
import logging
import base64
import uuid

from cord.configs import CordConfig
from cord.http.querier import Querier
from cord.orm.project import Project
from cord.orm.label_row import LabelRow
from cord.orm.model import Model, ModelInferenceParams
from cord.orm.labeling_algorithm import LabelingAlgorithm, ObjectInterpolationParams
from cord.utils.str_constants import *

# Logging configuration
logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)s] [%(funcName)s()] %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p'
                    )


class CordClient(object):
    """
    Cord client. Allows you to query db items associated
    with a project (e.g. label rows, datasets).
    """

    def __init__(self, querier, config):
        self._querier = querier
        self._config = config

    @staticmethod
    def initialise(project_id=None, api_key=None):
        """
        Creates and initializes a Cord client from a project ID and API key.

        Args:
            project_id: A project ID string. If None, obtained from the CORD_PROJECT_ID environment variable.
            api_key: A project API key. If None, obtained from the CORD_API_KEY environment variable.

        Returns:
            CordClient: A Cord client instance.
        """
        config = CordConfig(project_id, api_key)
        return CordClient.initialise_with_config(config)

    @staticmethod
    def initialise_with_config(config):
        """
        Creates and initializes a Cord client from a Cord config instance.

        Args:
            config: A Cord config instance.

        Returns:
            CordClient: A Cord client instance.
        """
        querier = Querier(config)
        return CordClient(querier, config)

    def get_project(self):
        """
        Retrieves project info (pointers to data, labels).

        Args:
            self: Cord client object.

        Returns:
            Project: A project record instance.

        Raises:
            AuthorisationError: If the project API key is invalid.
            ResourceNotFoundError: If no project exists by the specified project ID.
            UnknownError: If an error occurs while retrieving the project.
        """
        return self._querier.basic_getter(Project)

    def get_label_row(self, uid):
        """
        Retrieves label row

        Args:
            uid: A label_hash (uid) string.

        Returns:
            LabelRow: A label row instance.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no label exists by the specified label_hash (uid).
            UnknownError: If an error occurs while retrieving the label.
            OperationNotAllowed: If the read operation is not allowed by the API key.
        """
        return self._querier.basic_getter(LabelRow, uid)

    def save_label_row(self, uid, label):
        """
        Save existing label Row

        If you have a series of frame labels and have not updated answer
        dictionaries, call the construct_answer_dictionaries utils function
        to do so prior to saving labels.

        Args:
            uid: A label_hash (uid) string.
            label: A label row instance.

        Returns:
            Bool.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no label exists by the specified label_hash (uid).
            UnknownError: If an error occurs while saving the label.
            OperationNotAllowed: If the write operation is not allowed by the API key.
            AnswerDictionaryError: If an object or classification instance is missing in answer dictionaries.
            CorruptedLabelError: If a blurb is corrupted (e.g. if the frame labels have more frames than the video).
        """
        label = LabelRow(label)
        return self._querier.basic_setter(LabelRow, uid, payload=label)

    def model_inference(self,
                        uid,
                        file_paths=None,
                        base64_strings=None,
                        conf_thresh=0.6,
                        iou_thresh=0.3,
                        device="cuda",
                        detection_frame_range=None,
                        ):
        """
        Run inference with model trained on the platform.

        Args:
            uid: A model_iteration_hash (uid) string.
            file_paths: List of local file paths to image(s) or video(s) - if running inference on files
            base64_strings: List of base 64 strings of image(s) or video(s) - if running inference on base64 strings
            conf_thresh: Confidence threshold (default 0.6)
            iou_thresh: Intersection over union threshold (default 0.3)
            device: Device (CPU or CUDA, default is CUDA)
            detection_frame_range: Detection frame range (for videos)

        Returns:
            Inference results: A dict of inference results.

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            ResourceNotFoundError: If no model exists by the specified model_iteration_hash (uid).
            UnknownError: If an error occurs while running inference.
            FileTypeNotSupportedError: If the file type is not supported for inference (has to be an image or video)
            DetectionRangeInvalidError: If a detection range is invalid for video inference
        """
        if (file_paths is None and base64_strings is None) or (
                file_paths is not None and len(file_paths) > 0 and base64_strings is not None and len(
                base64_strings) > 0):
            raise Exception("To run model inference, you must pass either a list of files or base64 strings")

        if detection_frame_range is None:
            detection_frame_range = []

        files = []
        if file_paths is not None:
            for file_path in file_paths:
                file = open(file_path, 'rb').read()
                files.append({
                    "uid": file_path,  # Add file path as inference identifier
                    "base64_str": base64.b64encode(file).decode('utf-8')  # File to base64 string
                })

        elif base64_strings is not None:
            for base64_string in base64_strings:
                files.append({
                    "uid": str(uuid.uuid4()),  # Add uuid as inference identifier
                    "base64_str": base64_string.decode('utf-8')  # base64 string to utf-8
                })

        params = ModelInferenceParams({
            'files': files,
            'conf_thresh': conf_thresh,
            'iou_thresh': iou_thresh,
            'device': device,
            'detection_frame_range': detection_frame_range,
        })

        return self._querier.basic_setter(Model, uid, payload=params)

    def object_interpolation(self,
                             key_frames,
                             objects_to_interpolate,
                             ):
        """
        Run object interpolation algorithm with a platform defined project.

        Args:
            key_frames: Labels for frames to be interpolated
            objects_to_interpolate: List of object hashes of objects to interpolate

        Returns:
            Interpolation results: Full set of filled frames including interpolated objects

        Raises:
            AuthenticationError: If the project API key is invalid.
            AuthorisationError: If access to the specified resource is restricted.
            UnknownError: If an error occurs while running interpolation.
        """
        if len(key_frames) == 0 or len(objects_to_interpolate) == 0:
            raise Exception("To run object interpolation, you must pass key frames and objects to interpolate")

        interpolation_params = ObjectInterpolationParams({
            'key_frames': key_frames,
            'objects_to_interpolate': objects_to_interpolate,
        })

        params = LabelingAlgorithm({
            'algorithm_name': INTERPOLATION,
            'algorithm_parameters': interpolation_params,
        })

        return self._querier.basic_setter(LabelingAlgorithm, str(uuid.uuid4()), payload=params)
