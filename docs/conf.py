"""Sphinx configuration."""

project = "PyBuild Deps"
author = "Bruno Ciconelle"
copyright = "2023, Bruno Ciconelle"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
