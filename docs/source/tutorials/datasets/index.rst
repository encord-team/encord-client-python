.. include:: ../../substitutes.rst


********
Datasets
********

The |sdk| allows you to interact with the datasets you have added to |company|.
A dataset has the attributes ``title``, ``description``, ``dataset_type``, and ``data_rows``

.. code-block:: 

    {
        "title": "Example title",
        "description": "Example description ..",
        "dataset_type": "0",
        "data_rows": [
            {
                "data_hash": "<data_hash>",
                "data_title": "sample_data.mp4",
                "data_type": "VIDEO"
            }, {
                "data_hash": "<data_hash>",
                "data_title": "image-group-abcde",
                "data_type": "IMG_GROUP"
            },
            ...
        ]
    }

Note how the ``data_rows`` can both consist of videos and image groups.

Below, you can find tutorials on how to interact with your datasets.

.. toctree::
    :maxdepth: 2

    creating_a_dataset
    creating_dataset_api_keys
    fetching_dataset_api_keys
    listing_existing_datasets
    adding_data_to_datasets
    deleting_data_from_datasets
    re_encoding_videos_in_datasets
