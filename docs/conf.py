import sys
import os.path
import sphinx_rtd_theme

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx_tabs.tabs',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3.6', None),
    'aiopg': ('http://aiopg.readthedocs.io/en/stable', None),
    'sqlalchemy': ('http://docs.sqlalchemy.org/en/rel_1_1', None),
}

source_suffix = '.rst'
master_doc = 'index'

project = 'Hiku'
copyright = '2016, Vladimir Magamedov'
author = 'Vladimir Magamedov'

version = 'dev'
release = 'dev'

templates_path = ['_templates']

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']
