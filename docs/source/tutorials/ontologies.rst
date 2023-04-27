********
Ontologies
********

A central component of a project is the ontology - an in-depth description of which can be found `here <https://docs.encord.com/ontologies/overview>`_.

Ontologies are top-level entities that can be attached to projects that provide a template structure for labels. 
Please note that a project can only have a single ontology attached to it.

- For a platform description of the ontology, please see :xref:`configure_label_editor_(ontology)`.
- To access the ontology you can use the :meth:`~encord.user_client.EncordUserClient.get_ontology()` method, that allows you to work with its `structure` property.
- The structure comes as the :class:`~encord.ontology.ontology_labels_impl.OntologyStructure` class which has good self documenting examples on how to be used.

This section will cover some of the most common use cases for ontologies.

Copying an ontology
==================

An Ontology can be copied to be used in another project without the need to re-create all objects or classifications from scratch. 

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/ontologies/copying_ontology.py
            :language: python
