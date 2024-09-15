extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_inline_tabs",
]

autoclass_content = "both"
autodoc_member_order = "bysource"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.6", None),
    "aiopg": ("https://aiopg.readthedocs.io/en/stable", None),
    "sqlalchemy": ("http://docs.sqlalchemy.org/en/rel_1_1", None),
}

source_suffix = ".rst"
master_doc = "index"

project = "hiku"
copyright = "2019, Vladimir Magamedov"
author = "Vladimir Magamedov"

templates_path = []

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {}
