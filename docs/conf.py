import sys
import os.path
import sphinx_rtd_theme

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
extensions = ['sphinx.ext.autodoc']

source_suffix = '.rst'
master_doc = 'index'

project = 'Hiku'
copyright = '2016, Vladimir Magamedov'
author = 'Vladimir Magamedov'

version = 'dev'
release = 'dev'

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
