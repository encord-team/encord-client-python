.. include:: ../../substitutes.rst

******************
Creating a dataset
******************

You can use the |product| to create a dataset.
First, you need to create a :xref:`public-private_key_pair` for |company|.

You also need to select where your data will be hosted to select the appropriate :class:`DatasetType <encord.orm.dataset.DatasetType>`.
For example, the following example will create a dataset called "traffic data" that will expect data hosted on AWS S3.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/datasets/creating_a_dataset.py
            :language: python

    .. tab:: Example output

        .. code-block:: json

            {
                "title": "Traffic Data",
                "type": 1,
                "dataset_hash": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
            }

