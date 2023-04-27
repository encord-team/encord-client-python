********
Ontologies
********

A central component of a project is the ontology - an in-depth description of which can be found `here <https://docs.encord.com/ontologies/overview>`_.

The ontology essentially defines the label structure of a given project.

- For a platform description of the ontology, please see :xref:`configure_label_editor_(ontology)`.
- To access the ontology you can use the :meth:`~encord.user_client.EncordUserClient.get_ontology()` method.
    - This allows you to work with its `structure` property to read or write parts of the ontology.
- The structure comes as the :class:`~encord.ontology.ontology_labels_impl.OntologyStructure` class which has good self documenting examples on how to be used.

This section will cover some of the most common use cases for ontologies.

Copying an ontology
==================

An Ontology can be copied to be used in another project without the need to re-create all objects or classifications from scratch. 

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/ontologies/copying_ontology.py
            :language: python
