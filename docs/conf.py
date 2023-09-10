extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]

autoclass_content = 'both'
autodoc_member_order = 'bysource'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3.6', None),
    'aiopg': ('http://aiopg.readthedocs.io/en/stable', None),
    'sqlalchemy': ('http://docs.sqlalchemy.org/en/rel_1_1', None),
}

source_suffix = '.rst'
master_doc = 'index'

project = 'hiku'
copyright = '2019, Vladimir Magamedov'
author = 'Vladimir Magamedov'

templates_path = []

html_theme = 'furo'
html_static_path = ['_static']
html_theme_options = {
    'display_version': False,
}


def setup(app):
    app.add_css_file('style.css?r=1')
    app.add_css_file('fixes.css?r=1')
