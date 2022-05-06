.. include:: ../../../substitutes.rst

*************************
Fetching project ontology
*************************

You can fetch the |ontology| of an existing project for viewing via the |sdk|.
For a |platform|-related description of the |ontology|, please see :xref:`configure_label_editor_(ontology)`.

.. tabs::

    .. tab:: Code

        .. literalinclude:: /code_examples/tutorials/projects/fetching_project_ontology.py
            :language: python

    .. tab:: Example output

        .. code-block:: python

            {'classifications': [{'attributes': [{'featureNodeHash': '237c442f',
                                                  'id': '1.1',
                                                  'name': 'Radio Example',
                                                  'options': [{'featureNodeHash': '00fe752c',
                                                               'id': '1.1.1',
                                                               'label': 'Cat',
                                                               'value': 'cat'},
                                                              {'featureNodeHash': '0538f289',
                                                               'id': '1.1.2',
                                                               'label': 'Dog',
                                                               'value': 'dog'},
                                                              {'featureNodeHash': '4d2c4767',
                                                               'id': '1.1.3',
                                                               'label': 'Horse',
                                                               'value': 'horse'}],
                                                  'required': False,
                                                  'type': 'radio'}],
                                  'featureNodeHash': '21b68c3b',
                                  'id': '1'},
                                 {'attributes': [{'featureNodeHash': 'd7c2ad1b',
                                                  'id': '2.1',
                                                  'name': 'Checkbox example',
                                                  'options': [{'featureNodeHash': '88903c98',
                                                               'id': '2.1.1',
                                                               'label': 'check 1: are '
                                                                        'there people in '
                                                                        'the image',
                                                               'value': 'check_1:_are_there_people_in_the_image'},
                                                              {'featureNodeHash': 'a5c19b1b',
                                                               'id': '2.1.2',
                                                               'label': 'check if there is '
                                                                        'a pink elephant '
                                                                        'with cat eyes in '
                                                                        'the image',
                                                               'value': 'check_if_there_is_a_pink_elephant_with_cat_eyes_in_the_image'}],
                                                  'required': False,
                                                  'type': 'checklist'}],
                                  'featureNodeHash': '59151c93',
                                  'id': '2'},
                                 {'attributes': [{'featureNodeHash': '2afbce16',
                                                  'id': '3.1',
                                                  'name': 'Text example',
                                                  'required': False,
                                                  'type': 'text'}],
                                  'featureNodeHash': '8161c61a',
                                  'id': '3'}],
             'objects': [{'color': '#D33115',
                          'featureNodeHash': '41d0a534',
                          'id': '1',
                          'name': 'cat',
                          'shape': 'polygon'},
                         {'color': '#FCDC00',
                          'featureNodeHash': 'edf21536',
                          'id': '2',
                          'name': 'bus',
                          'shape': 'polygon'},
                         {'color': '#DBDF00',
                          'featureNodeHash': '2a9ab898',
                          'id': '3',
                          'name': 'airplane',
                          'shape': 'bounding_box'},
                         {'color': '#A4DD00',
                          'featureNodeHash': '56996de1',
                          'id': '4',
                          'name': 'bird',
                          'shape': 'point'}]}

