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

# Tried a variety of options, but this seems to work the best for auto-module
# reading of our scripts directory...
sys.path.insert(0, os.path.abspath("../../../mads_calibration"))
sys.path.insert(0, os.path.abspath("../../../scripts"))

# -- Project information -----------------------------------------------------

project = 'dvmdostem'
copyright = '2024, Tobey Carman, Ruth Rutter, Helene Genet, Eugenie Euskirchen'
author = 'Tobey Carman, Ruth Rutter, Helene Genet, Eugenie Euskirchen'

# The full version, including alpha/beta/rc tags
release = 'v0.8.3'
version = 'v0.8.3'


# -- General configuration ---------------------------------------------------

numfig = True # auto-numbering for figures, reference by name


# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
  'sphinx.ext.autosectionlabel',
  'sphinx_toolbox.collapse',
  'jupyter_sphinx', # executes inline ipython/jupyter notebook code...
  'sphinx.ext.autodoc',
  'bokeh.sphinxext.bokeh_plot',
  #'sphinx.ext.autosummary',
  #'sphinx.ext.automodule',
  #'numpydoc',
  'sphinx.ext.napoleon',
  'sphinxarg.ext',
  'sphinxcontrib.bibtex',
]

bibtex_bibfiles = ["bibliography.bib"]
bibtex_reference_style = "author_year"

# -- Config for some extensions ----------------------------------------------
autosectionlabel_prefix_document = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

#numpydoc_use_plots = False

napoleon_google_docstring = False
napoleon_numpy_docstring = True
# napoleon_include_init_with_doc = False
# napoleon_include_private_with_doc = False
# napoleon_include_special_with_doc = True
# napoleon_use_admonition_for_examples = False
# napoleon_use_admonition_for_notes = False
# napoleon_use_admonition_for_references = False
# napoleon_use_ivar = False
# napoleon_use_param = True
# napoleon_use_rtype = True
# napoleon_preprocess_types = False
# napoleon_type_aliases = None
# napoleon_attr_annotations = True


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    #'analytics_id': 'G-XXXXXXXXXX',  #  Provided by Google in your dashboard
    #'analytics_anonymize_ip': False,
    # 'logo_only': False,
    'display_version': True,
    # 'prev_next_buttons_location': 'bottom',
    # 'style_external_links': False,
    # 'vcs_pageview_mode': '',
    # 'style_nav_header_background': 'white',
    # Toc options
    # 'collapse_navigation': True,
    # 'sticky_navigation': True,
    # 'navigation_depth': 4,
    # 'includehidden': True,
    # 'titles_only': False
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    'custom_styles.css',
]
