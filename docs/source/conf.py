# (C) Copyright 2018-2024 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

# Traits Futures documentation build configuration file, created by
# sphinx-quickstart on Sun Jul 29 10:49:55 2018.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import importlib.metadata

import enthought_sphinx_theme

# -- General configuration ------------------------------------------------

# Sphinx versions older than 3.5 run into issues with the autodoc_mock_imports
# setting below.
needs_sphinx = "3.5"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "traits.util.trait_documenter",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = []

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "Traits Futures"
copyright = "2018-2024 Enthought, Inc., Austin, TX"
author = "Enthought"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
release = importlib.metadata.version("traits-futures")
version = release = ".".join(release.split(".")[:2])

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# Don't include parentheses after function and method names.
add_function_parentheses = False

# Do use nitpicky mode: we want to know about broken references.
nitpicky = True

# Ignore complaints about references to classes in wx and pyface.qt.QtCore
nitpick_ignore = [
    # Exclusions needed for Sphinx < 4.
    ("py:class", "pyface.qt.QtCore.QObject"),
    ("py:class", "wx.App"),
    ("py:class", "wx.EvtHandler"),
    ("py:class", "wx.Timer"),
    # These two slightly strange class descriptions (note the trailing dot)
    # appear with Sphinx >= 4. This may be a bug in Sphinx.
    ("py:class", "pyface.qt.QtCore."),
    ("py:class", "wx."),
]

# Options for Sphinx copybutton extension
# ---------------------------------------

# Matches prompts - "$ ", ">>>" and "..."
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

# -- Options for Napoleon extension ---------------------------------------

# Do pre-process NumPyDoc - style type strings. This prevents warnings
# resembling "py:class reference target not found: optional".
napoleon_preprocess_types = True

# Other terms that might appear in type strings.
napoleon_type_aliases = {
    "CallFuture": ":class:`~.CallFuture`",
    "IEventLoop": ":class:`~.IEventLoop`",
    "IEventLoopHelper": ":class:`~.IEventLoopHelper`",
    "IFuture": ":class:`~.IFuture`",
    "IMessageRouter": ":class:`~.IMessageRouter`",
    "IMessageSender": ":class:`~.IMessageSender`",
    "IParallelContext": ":class:`~.IParallelContext`",
    "IPingee": ":class:`~.IPingee`",
    "ITaskSpecification": ":class:`~.ITaskSpecification`",
    "IterationFuture": ":class:`~.IterationFuture`",
    "MultiprocessingRouter": ":class:`~.MultiprocessingRouter`",
    "MultithreadingRouter": ":class:`~.MultithreadingRouter`",
    "ProgressFuture": ":class:`~.ProgressFuture`",
    "TraitsExecutor": ":class:`~.TraitsExecutor`",
}

# -- Options for Graphviz extension ---------------------------------------

# Output format when building HTML files
graphviz_output_format = "svg"

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme_path = [enthought_sphinx_theme.theme_path]

html_theme = "enthought"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "TraitsFuturesdoc"


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "TraitsFutures.tex",
        "Traits Futures Documentation",
        "Enthought",
        "manual",
    ),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, "traitsfutures", "Traits Futures Documentation", [author], 1)
]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "TraitsFutures",
        "Traits Futures Documentation",
        author,
        "TraitsFutures",
        "One line description of project.",
        "Miscellaneous",
    ),
]

# Options for autodoc extension
# -----------------------------

autodoc_mock_imports = ["pyface.qt", "wx"]


# Options for intersphinx extension
# ---------------------------------

intersphinx_mapping = {
    "pyface": ("https://docs.enthought.com/pyface", None),
    "python": ("https://docs.python.org/3", None),
    "traits": ("https://docs.enthought.com/traits", None),
    "traitsui": ("https://docs.enthought.com/traitsui", None),
}


def run_apidoc(app, config):
    """
    Hook to generate API documentation via sphinx-apidoc

    Parameters
    ----------
    app : the Sphinx application
    config : the Sphinx configuration
    """
    import pathlib

    import sphinx.ext.apidoc

    source_dir = pathlib.Path(__file__).parent
    project_root = source_dir.parent.parent
    target_dir = project_root / "traits_futures"

    exclude_patterns = [
        target_dir / "tests" / "*.py",
        target_dir / "*" / "tests" / "*.py",
    ]

    args = [
        "--separate",
        "--no-toc",
        "--templatedir",
        source_dir / "api" / "templates",
        "-o",
        source_dir / "api",
        target_dir,
        *exclude_patterns,
    ]

    sphinx.ext.apidoc.main([str(arg) for arg in args])


def setup(app):
    app.connect("config-inited", run_apidoc)
