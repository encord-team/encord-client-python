.. include:: ../../substitutes.rst

*************
Deleting Data
*************

You can remove both Videos and Image Groups from datasets created using both the |platform| and the |sdk|.
Use the method :meth:`dataset_client.delete_data() <.EncordClientDataset.delete_data>` to delete from a dataset.

.. autolink-concat:: section

.. autolink-preface::

    from encord.client import EncordClientDataset
    dataset_client = EncordClientDataset()

.. code-block:: python

    dataset_client.delete_data(
        [
            "<video1_data_hash>",
            "<image_group1_data_hash>",
        ]
    )


In case the Video or Image Group belongs to |company|-hosted storage, the corresponding file shall be removed from the Encord-hosted storage.

Please ensure that the list contains Videos/Image Groups from the same dataset which is used to initialise the :class:`dataset_client <.EncordClientDataset>`.
Any Videos or Image Groups which do not belong to the dataset used for initialisation would be ignored.

