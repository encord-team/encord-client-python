******
Labels
******

.. note::
    This page is undergoing a reconstruction [Monday, May 9th 2022].

A label row has the attributes ````label_hash```` uid, ``data_title``, ``data_type``, ``data_units``, and ``label_status``.

.. code-block::

    {
        'label_hash': label_hash (uid),
        'data_title': data_title,
        'data_type': data_type,
        'data_units': data_units,
        'object_answers': object_answers,
        'classification_answers': classification_answers,
        'label_status': label_status,
    }

A label row contains a data unit or a collection of data units and associated labels, and is specific to a data asset with type video or image group.

1.  A label row with a data asset of type ``video`` contains a single data unit.
2.  A label row with a data asset of type ``img_group`` contains any number of data units.

A data unit can have any number of vector labels (e.g. bounding box, polygon, keypoint) and classifications.

Before you start, make sure that a project client is initialised with the appropriate project ID and API key.

.. code-block::

    from encord.client import EncordClient

    client = EncordClient.initialise("<project_id>", "<project_api_key>")


Getting label rows
==================

Project label row IDs (``label_hash`` uid) are found in the project information Python JSON (``client.get_project()``), which also contain information about the data title (``data_title``), data type (``data_type``) and label status (``label_status``).

.. code-block::

    {
        ...,
        'label_rows': [{
            'label_hash': 'sample_label_uid',
            'data_hash': 'sample_data_uid',
            'dataset_hash': 'sample_dataset_uid',
            'dataset_title': 'sample_dataset_title',
            'data_title': 'sample_data.mp4',
            'data_type': 'VIDEO',
            'label_status': 'LABELLED',
        }, {
            'label_hash': ...,
        }]
    }


Use the client to fetch individual label objects.

.. code-block::

    label = client.get_label_row('sample_label_uid')

Use the ``project.get_labels_list()`` method to get a list each label ID (``label_hash`` uid) in a project and conveniently fetch all project labels.

.. code-block::

    project = client.get_project()

    label_rows = []
    for label_hash in project.get_labels_list():
        lb = client.get_label_row(label_hash)
        label_rows.append(lb)

The label row object contains data units with signed URL's (``data_link``) to the labeled data asset.


.. code-block::

    {
        'label_hash': 'sample_label_uid',
        'data_hash': 'sample_data_uid',
        'data_type': 'sample_data_type',
        'data_units': {
            ...,
            'sample_data_hash': {
                'data_hash': 'sample_data_hash',
                'data_title': 'sample_data_title',
                'data_link': 'sample_data_link',
                'data_type': 'sample_data_type',
                'data_fps': 'sample_dat_fps' # For video
                'data_sequence': 'sample_sequence_number',
                'labels': {
                    ...
                },
            },
        },
        'object_answers': {
            ...
        },
        'classification_answers': {
            ...
        }
    }

The objects and classifications answer dictionaries contain classification 'answers' (i.e. attributes that describe the object or classification).
This is to avoid storing the information at every frame in the label dictionary.

For the ``video`` data type, the ``labels`` dictionary contains a series of frames.

.. code-block::

    {
        'frame': {
            'objects': {
                [{object 1}, {object 2}, ...]
            }
            'classifications': {
                [{classification 1}, {classification 2}, ...]
            }
        },
        ...
    }

For the ``img_group`` data type, the ``objects`` and ``classifications`` are spread in ``labels``.

Each frame entry in the labels dictionary must have an ``objects`` and ``classifications`` key with a list of objects and classifications.
For videos, frames must be in a linearly ordered set.

.. code-block::

    {
        'frame': {
            'objects': [{...}],
            'classifications': [{...}],
        },
    }

The ``object answers`` dictionary is in the form:

.. code-block::

    {
        'objectHash': {
            'objectHash': objectHash,
            'classifications': [{answer 1}, {answer 2}, ...]
        },
        ...
    }

The ``classification answers`` dictionary is in the form:


.. code-block::

    {
        'classificationHash': {
            'classificationHash': classificationHash,
            'classifications': [{answer 1}, {answer 2}, ...]
        },
        ...
    }


Saving label rows
=================

Labels are saved to their label row ID (``label_hash`` uid) from a label row instance.
In case you want to save labels for the data which was not labeled before, follow the steps under "Creating label rows" below.

.. code-block::

    client.save_label_row('sample_label_uid', sample_label)

Label rows have to be saved in the same format as fetched.
The function ``construct_answer_dictionaries`` helps construct answer dictionaries for all objects and classifications in the label row if they do not exist, returning a label row object with updated object and classification answer dictionaries.

First, import the label_utilities library.

.. code-block::

    from encord.utilities import label_utilities

Then, save labels.

.. code-block::

    sample_label = client.get_label_row('sample_label_uid')

updated_label = label_utilities.construct_answer_dictionaries(sample_label)
client.save_label_row('sample_label_uid', updated_label)


Creating a label row
====================

If you want to save labels to a unit of data (``video``, ``img_group``) for which a label row (and thus a ``label_hash`` uid) does not exist yet, you need to create a label row associated with the data.

1.  Get the data_hash (``data_hash`` uid) that you want to create labels for. For this, request all label rows and note the ones that are NOT_LABELLED under 'label_status' (or, where ``label_hash`` is None):

.. code-block::

    project = client.get_project()
    print(project.label_rows)

In an example project, we have two videos.
The first was not labeled, and therefore, you should use its ``data_hash`` uid to create a new label row for this video.


.. code-block::

    [
      {
      'label_hash': None,
      'data_hash': '<data_hash>',
      'data_title': 'sample_video_1.mp4',
      'cord_type': 0,
      'data_type': 'VIDEO',
      'label_status': 'NOT_LABELLED'
      },
      {
      'label_hash': '<label_hash>',
      'data_hash': '<data_hash>',
      'data_title': 'sample_video_2.mp4',
      'cord_type': 0,
      'data_type': 'VIDEO',
      'label_status': 'LABELLED'
      }
    ]


2.  Create the label row:

.. code-block::

    data_hash = '<data_hash>'
    my_label_row = client.create_label_row(data_hash)


The label row will have the familiar structure, and can be updated as needed.
You can retrieve its uid via ``my_label_row.label_hash`` and run other operations such as get and save.

Submitting a label row for review
=================================

The following method can be used in case you want to submit a label row for review.

.. code-block::

    client.submit_label_row_for_review('sample_label_uid')

The above method will submit the annotation task corresponding to the label row and create the review tasks corresponding to it based on the sampling rate in the project settings.

Getting data rows
=================

A data row unit contains a data unit, or a collection of data units, and has attributes ``data_hash`` uid, ``video``, and ``images``.


.. code-block::

    {
        'data_hash': data_hash (uid),
        'video': video,
        'images': images,
    }


1.  A data row with a data asset of type ``video`` contains a single data unit in the form of a video.
2.  A data row with a data asset of type ``img_group`` contains any number of data units in the form of images.

Before you start, make sure that a project client is initialised with the appropriate project ID and API key.

.. code-block::

    data_row = client.get_data('sample_data_uid', generate_signed_url=True)

You can optionally return signed URLs for timed public access to that resource (default is False).

Reviewing label logs
====================

You can query information about a project's labels by using the ``get_label_logs`` method of a client initialised for that project.
You will need an API key with the``label_logs.read`` permission.
The ``get_label_logs`` takes a number of optional parameters to narrow down the retrieved logs:

.. code-block::

    from encord.client import EncordClient

    client = EncordClient.initialise("<project_id>", "<project_api_key>")
    logs = client.get_label_logs(user_hash=<user_hash>)
    for log in logs:
        print(log)

.. code-block::

    def get_label_logs(
        self,
        user_hash: str = None,
        data_hash: str = None,
        from_unix_seconds: int = None,
        to_unix_seconds: int = None
        )
        -> List[LabelLog]