# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

# build docs using nltk from the upper dir, not the installed version
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "Home"
copyright = "2021, Tom Aarsen"
author = "Tom Aarsen"

# The full version, including alpha/beta/rc tags
release = "0.1.5"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["api/modules.rst"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "nltk_theme"

html_theme_options = {"navigation_depth": 1}
# Required for the theme, used for linking to a specific tag in the website footer
html_context = {"github_user": "tomaarsen", "github_repo": "module_dependencies"}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


def run_apidoc(app):
    """Generage API documentation"""
    import better_apidoc

    better_apidoc.APP = app
    better_apidoc.main(
        [
            "better-apidoc",
            "-t",
            os.path.join(".", "docs", "_templates"),
            "--force",
            "--separate",
            "-o",
            os.path.join(".", "docs", "api"),
            os.path.join(".", "module_dependencies"),
        ]
    )


def setup(app):
    app.connect("builder-inited", run_apidoc)


# -- Options for Autodoc output ------------------------------------------------
# If it's "mixed", then the documentation for each parameter isn't listed
# e.g. nltk.tokenize.casual.TweetTokenizer(preserve_case=True, reduce_len=False, strip_handles=False, match_phone_numbers=True)
# and that's it.
# With "seperated":
# nltk.tokenize.casual.TweetTokenizer
# ...
# __init__(preserve_case=True, reduce_len=False, strip_handles=False, match_phone_numbers=True)
#     Create a TweetTokenizer instance with settings for use in the tokenize method.
#     Parameters
#         preserve_case (bool) – Flag indicating whether to preserve the casing (capitalisation) of text used in the tokenize method. Defaults to True.
#         reduce_len (bool) – Flag indicating whether to replace repeated character sequences of length 3 or greater with sequences of length 3. Defaults to False.
#         strip_handles (bool) – Flag indicating whether to remove Twitter handles of text used in the tokenize method. Defaults to False.
#         match_phone_numbers (bool) – Flag indicating whether the tokenize method should look for phone numbers. Defaults to True.
autodoc_class_signature = "separated"

# Put the Python 3.5+ type hint in the signature and also at the Parameters list
autodoc_typehints = "both"

autodoc_inherit_docstrings = True

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "show-inheritance": True,
    "undoc-members": True,
    # 'exclude-members': '__weakref__'
    "ignore-module-all": True,
    "inherited-members": True,
    "no-inherited-members": True,
}
