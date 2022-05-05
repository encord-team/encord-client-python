.. include:: ../../substitutes.rst

********
Projects
********

We have divided the project tutorials into a couple of subsets.
First, we show general concepts like creating a new project from the |product|.
Afterwards, we go more into details with working with, e.g., labels,
and our integrated automation models and algorithms.

General
=======
In this section, we include simple code examples to interact with the "metadata" of projects.
With metadata we mean things that do not involve labels or the ontology of the project.
Specifically, the following tutorials revolve around API keys, datasets and users associated to the project.

.. toctree::
    :maxdepth: 4

    creating_a_project
    listing_existing_projects
    creating_a_project_api_key
    fetching_project_api_keys
    adding_datasets_to_projects
    removing_datasets_from_projects
    adding_users_to_projects


Ontology
========
A central component of a project is the |ontology|.
In short, the ontology defines how the label structure of a given project.
For a |platform|-related description of the |ontology|, please see :xref:`configure_label_editor_(ontology)`.

.. toctree::
    :maxdepth: 3

    ./ontology/fetching_project_ontology


Labels
======

.. toctree::
    :maxdepth: 3

    ./labels/reading_label_rows
    ./labels/creating_label_rows
    ./labels/updating_label_rows
    ./labels/reading_label_logs


Models
======

.. toctree::
    :maxdepth: 3

    ./models/creating_and_training_a_model
    ./models/running_model_inference


Algorithms
==========

.. toctree::
    :maxdepth: 3

    ./algorithms/running_object_interpolation


Other Resources
===============

.. toctree::
    :maxdepth: 3

    ./other/importing_cvat_annotations


