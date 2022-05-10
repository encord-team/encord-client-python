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
sys.path.insert(
    0,
    os.path.abspath("../../venv/lib/python3.7/site-packages"),
)
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
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "sphinx_tabs.tabs",
    "sphinx_codeautolink",
    "sphinx_copybutton",
    "xref",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["../_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


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

# Static links
with open(os.path.abspath("./links.json")) as f:
    xref_links = json.load(f)
