********
Ontologies
********

A central component of a project is the ontology - an in-depth description of which can be found `here <https://docs.encord.com/docs/annotate-ontologies>`_.

Ontologies are top-level entities that can be attached to projects that provide a template structure for labels.
Please note that while a project can only have a single ontology attached to it, one ontology can be attached to multiple projects.

- To access the ontology you can use the :meth:`~encord.user_client.EncordUserClient.get_ontology()` method, that allows you to work with its `structure` property.
- The structure comes as the :class:`~encord.ontology.ontology_labels_impl.OntologyStructure` class which has good self documenting examples on how to be used.

This section will cover some of the most common use-cases for ontologies.

Copying an ontology
==================

Copying an ontology allows you to make changes to the stucture without affecting the projects the original ontology is attached to.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/ontologies/copying_ontology.py
            :language: python
