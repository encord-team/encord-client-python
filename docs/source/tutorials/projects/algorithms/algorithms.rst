**********
Algorithms
**********

.. note::
    This page is undergoing a reconstruction [Monday, May 9th 2022].

The Python SDK allows you to interact with the Encord algorithmic automation features.
Our library includes sampling, augmentation, transformation, and labeling algorithms.

To get started with our algorithmic automation features, make you have created an API key with ``algo.library`` added to access scopes and initialised a project client with the appropriate project ID and API key.

.. code-block::

    from encord.client import EncordClient
    client = EncordClient.initialise("<resource_id>", "<resource_api_key>")



Object interpolation
====================

The client object interpolator allows you to run interpolation algorithms on project labels (requires an editor ontology).

Interpolation is supported for the ontological types:

1.  Bounding box
2.  Polygon
3.  Keypoint

Use the ``client.object_interpolation(key_frames, objects_to_interpolate)`` method to run object interpolation.

Key frames (``key_frames``) can be obtained from a label row for the ``video`` data type.
The objects to interpolate between key frames is a list object IDs (``objectHash`` uid) contained within the ``labels`` dictionary.

An object is interpolated between the key frames where it is present, and is based on its object ID.

The interpolation algorithm can be run on multiple objects with different ontological objects at the same time (i.e. you can run interpolation on bounding box, polygon, and keypoint, using the same function call) on any number of key frames.


.. code-block::

    # Fetch label row
    sample_label = client.get_label_row('sample_label_uid')

    # Prepare interpolation
    key_frames = sample_label['data_units']['sample_data_hash']['labels']
    objects_to_interpolate = ['sample_object_uid']

    # Run interpolation
    interpolation_result = client.object_interpolation(key_frames, objects_to_interpolate)
    print(interpolation_result)

The interpolation algorithm can also be run from sample key frames kept locally, with ``key_frames`` passed in a simple JSON structure.

All that is required is a feature ID (``featureHash`` uid) and object ID (``objectHash`` uid) for each object in your set of key frames.

.. code-block::

    {
        "frame": {
            "objects": [
                {
                    "objectHash": object_uid,
                    "featureHash": feature_uid (from editor ontology),
                    "polygon": {
                        "0": {
                            "x": x1,
                            "y": y1,
                        },
                        "1": {
                            "x": x2,
                            "y": y2,
                        },
                        "2" {
                            "x": x3,
                            "y": y3,
                        },
                        ...,
                    }
                },
                {
                    ...
                }
            ]
        },
        "frame": {
            ...,
        }
    }

