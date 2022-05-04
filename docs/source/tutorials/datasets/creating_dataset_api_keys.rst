.. include:: ../../substitutes.rst

**************************
Creating a dataset API key
**************************

Via the |product| you can create a dataset-specific API key.
The API key is one way to :ref:`authentication:Authenticate with Encord`.
You need to provide the ``dataset_hash``, which uniquely identifies a dataset (see, e.g., the :ref:`tutorials/datasets/listing_existing_datasets:Listing existing datasets` to get such hash).
If you haven't created a dataset already, you can have a look at :ref:`tutorials/datasets/creating_a_dataset:Creating a Dataset`.

.. autolink-concat:: section

.. autolink-preface::
    from encord.orm.dataset_api_keys import DatasetAPIKey
    from encord.orm.dataset import DatasetScope


.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/creating_a_dataset_api_key.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            DatasetAPIKey(
              dataset_hash="<dataset_hash>",
              api_key="<api_key>",
              title="Example api key title",
              scopes=[
                  DatasetScope.READ,
                  DatasetScope.WRITE,
              ]
            )


.. note:: 

    This capability is available to only the Admin of a dataset.


With the API key at hand, you can use :ref:`authentication:API key authentication`.