# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import json

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../_extensions"))

# -- Project information -----------------------------------------------------

project = "Encord Python SDK"
copyright = "2022, Encord"
author = "Denis Gavrielov, Frederik Hvilshøj"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",  # https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html include documentation from doc strings.
    "sphinx.ext.coverage",  # https://www.sphinx-doc.org/en/master/usage/extensions/coverage.html collects doc coverage. Could be removed?
    "sphinx.ext.napoleon",  # https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html support for google doc strings
    "sphinx.ext.viewcode",  # https://www.sphinx-doc.org/en/master/usage/extensions/viewcode.html creates back links to source code.
    "sphinx.ext.autosectionlabel",  # https://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html each section header becomes its ref.
    "sphinx_autodoc_typehints",  # https://sphinx-toolbox.readthedocs.io/en/latest/extensions/more_autodoc/typehints.html automatically add type hints
    "sphinx_copybutton",  # https://sphinx-copybutton.readthedocs.io/en/latest/ adds copy button to code blocks.
    "sphinx_gallery.gen_gallery",  # https://sphinx-gallery.github.io/stable/index.html# build an example gallary, like in end-to-end tutorials landing page
    # ^ Also responsible for converting the end-to-end .py tutorials to sphinx docs.
    "sphinx_codeautolink",  # https://pypi.org/project/sphinx-codeautolink/ - link back to source code examples
    "sphinx_tabs.tabs",  # https://sphinx-tabs.readthedocs.io/en/latest/ - for tabs support
    "xref",
    "sphinx_toolbox.more_autodoc.overloads",  # https://sphinx-toolbox.readthedocs.io/en/latest/extensions/more_autodoc/overloads.html - support for nice documentation of overloads.
    # ^ this does not seem to be working.
]

highlight_language = "python3"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["../_templates"]


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "source/code_examples/tutorials/end-to-end/README.rst",
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["../_static"]

autodoc_member_order = "bysource"

# use :class:`<filename>:<Section Name>` instead of `<Section Name>` which
# could collide.
autosectionlabel_prefix_document = True

# Show tables in the autodoc of examples where definitions are used, e.g., in
# tutorials.
codeautolink_autodoc_inject = True


# == THEME CONFIG SECTION == #
html_favicon = "../_static/logo.svg"
html_logo = "../_static/logo.svg"
html_css_files = ["css/custom.css"]

html_theme_options = {
    "show_nav_level": 1,
    "show_toc_level": 2,
    "navbar_start": ["encord-navbar-logo"],
    "navbar_center": [],
}

html_sidebars = {
    "**": [
        "search-field",
        "encord-sidebar-nav-bs",
        "sidebar-ethical-ads",
    ]
}

# == END THEME SECTION == #

sphinx_gallery_conf = {
    "examples_dirs": "code_examples/tutorials/end-to-end",
    "gallery_dirs": "tutorials/end-to-end",
    "default_thumb_file": "source/images/end-to-end-thumbs/default.png",
    "line_numbers": False,
    "remove_config_comments": True,
    "min_reported_time": 10,
    "doc_module": ("encord",),
    "reference_url": {
        "encord": None,
    },
}

# Static links
with open(os.path.abspath("./links.json")) as f:
    xref_links = json.load(f)
