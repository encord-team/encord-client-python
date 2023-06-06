**********
Bitmask annotations
**********

`Bitmask` is a type of annotation on the Encord platform. It allows to perform pixel-wise segmentation of an image,
which is required when bounding boxes and polygons are not providing enough precision.

1. Downloading bitmask annotations from Encord
====================================

Encord UI allows to create Bitmask annotations. After labelling is complete, it is possible to download
these annotations using SDK.
Fol code example illustrates how to download bitmask and save it to a file:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/bitmasks/bitmask-download-example.py
            :language: python


2. Uploading bitmasks annotations to Encord
====================================

If there are pre-existing bitmask annotations, previously created in Encord or any other software,
they can be uploaded to Encord using the SDK.
The following code example illustrates how to read a bitmask from a file, and upload it:

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/bitmasks/bitmask-upload-example.py
            :language: python
