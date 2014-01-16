#!/usr/bin/python3

import sys, os
sys.path.insert(0, os.path.abspath('..'))

extensions = ['sphinx.ext.autodoc']
templates_path = ['_templates']

source_suffix = '.rst'
master_doc = 'index'

project = 'Mosgortrans Parser'
copyright = '2014, Dmitry Shachnev'
version = '0.1'
release = '0.1.0'

exclude_patterns = ['_build']

html_theme = 'nature'
html_static_path = ['_static']
