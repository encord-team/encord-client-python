.. Encord Python SDK documentation master file, created by
   sphinx-quickstart on Thu Jan  6 16:34:08 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: ./substitutes.rst


Welcome to the |company| Python SDK reference!
==============================================

To use the |company| Python SDK, you first need to have a way to authenticate the client.
If you haven't logged in to the platform and added a :xref:`public-private_key_pair`, please do so before using the |sdk|.

Before you start
""""""""""""""""
Please take a note of the following naming convention.


When we include ``"<some_name>"``, both in code examples and in text, we mean a string with a specific value which is defined by the context *without the "<" and the ">"*.
For example, ``"<project_hash>"`` would be the unique uid defining your project.

*In our examples, we will write:*

.. code-block:: python

   project_hash = "<project_hash>"

*In your code, you will write:*::

    project_hash = "00000000-1111-2222-3333-eeeeeeeeeeee"

In our docs, it should always be clear where to find such values and what the format should be.

Getting started
"""""""""""""""

Here are some resources to get you started with the |sdk|:

.. toctree::
   :maxdepth: 1

   quickstart
   general_concepts
   installation
   authentication


Tutorials
=========
Please find our documentation on how to perform specific actions below.

.. toctree::
   :maxdepth: 3

   tutorials


SDK Reference
=============
.. toctree::
   :maxdepth: 2

   api

Changelog
==========

.. toctree::

   Changelog <https://github.com/encord-team/encord-client-python/releases>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
