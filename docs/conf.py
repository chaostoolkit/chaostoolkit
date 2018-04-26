#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Configure the Sphinx project settings.

    Sphinx assumes that chaostoolkit is installed using
    ``python setup.py install`` so that it can read the version number.
    This project also uses the new ``m2r`` markdown converter from
    https://github.com/miyakogi/m2r#sphinx-integration

"""
import os
import sys
from chaostoolkit import __version__
sys.path.insert(0, os.path.abspath('../'))

# -- General configuration ------------------------------------------------

extensions = ['sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'm2r'
    ]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ['.rst', '.md', '.txt']

# The master toctree document.
master_doc = 'index'
html_theme = 'sphinx_rtd_theme'

# General information about the project.
project = 'chaostoolkit'
copyright = '2018'
author = 'chaostoolkit'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = __version__ 
# The full version, including alpha/beta/rc tags.
release = '0.1'
language = None
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
pygments_style = 'sphinx'
todo_include_todos = True

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'chaostoolkit', 'chaostoolkit',
     [author], 1)
]

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'https://docs.python.org/': None}
