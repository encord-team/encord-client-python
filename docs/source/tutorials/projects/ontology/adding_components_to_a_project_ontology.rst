.. include:: ../../../substitutes.rst

***************************************
Adding components to a project ontology
***************************************

The ontology has two overall types of components, classifications and objects.
Classifications relate to whole frames.
For example, if want to be able to annotate if an image if a of a cat or a dog as a whole, you will add an animal classification with options "Cat" and "Dog."
Objects, on the other hand, are specific to locations in a frame.
For example, if you want to annotate where is the dog in the image, you would first add an object to the ontology.
Objects could for example be a bounding box or a polygon indicating where the dog is.
In the following subsections, we will show you how both scenarios are done.


Adding a classification to a project ontology
=============================================
Here, we are in the "cat vs. dog" scenario from above.
Adding classifications for cats and dogs to an ontology via the |sdk| is done as follows.

The :meth:`add_classification() <.EncordClientProject.add_classification>` method takes the following parameters:

* ``name`` the description of the classification
* ``classification_type`` a value from the :class:`.ClassificationType` enum.
* ``required`` - a boolean value specifying whether the classification is mandatory
* ``options`` - a list of options that the annotator can choose from in case of :class:`CHECKLIST <.ClassificationType>`/:class:`RADIO <.ClassificationType>`.
  Omit this parameter if adding a ``TEXT`` classification.


.. literalinclude:: /code_examples/tutorials/projects/adding_classifications_to_a_project_ontology.py
    :language: python


Adding an object to a project ontology
======================================
Here, we are in the "where is the dog" scenario from above.
Adding objects to an existing ontology via the |sdk| is demonstrated in the following example.
The :meth:`add_object() <.EncordClientProject.add_object>` method takes the following parameters:

* ``name`` the name of the object as a string,
* ``shape`` the shape of the object, which is an :class:`.ObjectShape` enum.

.. literalinclude:: /code_examples/tutorials/projects/adding_objects_to_a_project_ontology.py
    :language: python


