**********
Bitmask annotations
**********

A `Bitmask` is a type of annotation on the Encord platform that allows for pixel-wise segmentation of an image,
which is required when bounding boxes and polygons are not providing enough precision.

1. Downloading bitmask annotations from Encord
====================================

The Encord UI allows the creation of Bitmask annotations. After labelling is complete, it is possible to download
these annotations using the SDK.
The following code example illustrates how to download and save bitmask labels:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/bitmasks/bitmask-download-example.py
            :language: python


2. Uploading bitmask annotations to Encord
====================================

If there are pre-existing bitmask annotations, previously created in Encord or any other software,
they can be uploaded to Encord using the SDK.
The following code example illustrates how to read a bitmask from a file, and upload it:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/bitmasks/bitmask-upload-example.py
            :language: python
