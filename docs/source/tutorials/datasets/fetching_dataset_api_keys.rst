.. include:: ../../substitutes.rst

*************************
Fetching dataset API keys
*************************

Via the |product|, you can get all API keys for an existing dataset.
You need to provide the ``dataset_hash`` which uniquely identifies a dataset (see, e.g., the :ref:`tutorials/datasets/listing_existing_datasets:Listing existing datasets` to get such hash).
If you haven't created a dataset already, you can have a look at :ref:`tutorials/datasets/creating_a_dataset:Creating a Dataset`.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/fetching_dataset_api_keys.py
            :language: python

    .. tab:: Example output

        .. code-block::

            [
                DatasetAPIKey(
                  dataset_hash="<dataset_hash>",
                  api_key="<dataset_api_key>",
                  title="Full Access API Key",
                  scopes=[
                      <DatasetScope.READ: "dataset.read">,
                      <DatasetScope.WRITE: "dataset.write">
                  ]
                ),
                ...
            ]

With the API key at hand, you can use :ref:`authentication:API key authentication`.