.. include:: ../../substitutes.rst

Fetching dataset API keys
=========================

Via the |product|, you can get all API keys for an existing dataset.
You need to provide the ``dataset_hash`` which uniquely identifies a dataset (see, e.g., the :ref:`tutorials/datasets/listing_existing_datasets:Listing existing datasets` to get such hash).


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/fetching_dataset_api_keys.py
            :language: python

    .. tab:: Example output

        .. code-block::

            [
                DatasetAPIKey(
                  dataset_hash='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
                  api_key='lCuoabcdefabcdefabcdefabcdefabcdefabc-jlan8',
                  title='Full Access API Key',
                  scopes=[
                      <DatasetScope.READ: 'dataset.read'>,
                      <DatasetScope.WRITE: 'dataset.write'>
                  ]
                ),
                ...
            ]


.. Note::

    This capability is available to only the Admin of a dataset.