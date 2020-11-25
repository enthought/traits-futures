# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import os

import pkg_resources

# Main package name, used for installing development sources
# and as a flake8 target.
PACKAGE_NAME = "traits_futures"

# Prefix used for generated EDM environments.
PREFIX = PACKAGE_NAME.lower().replace("_", "-")

# Platforms
MACOS = "osx-x86_64"
LINUX = "rh7-x86_64"
WINDOWS = "win-x86_64"

# Python versions
PYTHON36 = "py36"
PYTHON_VERSIONS = [PYTHON36]

# Toolkits
NULL = "null"  # no GUI toolkit; a simulated event loop is used for tests
PYQT = "pyqt"  # Qt 4, PyQt
PYQT5 = "pyqt5"  # Qt 5, PyQt
PYSIDE2 = "pyside2"  # Qt 5, Qt for Python
WXPYTHON = "wxpython"  # wxPython
TOOLKITS = [NULL, PYQT, PYQT5, PYSIDE2, WXPYTHON]

# Default Python version and toolkit.
DEFAULT_PYTHON = PYTHON36
DEFAULT_TOOLKIT = PYSIDE2

# Location of repository root. Assumes that the ci script is being
# run from the root of the repository.
ROOT_DIR = os.path.abspath(".")
PACKAGE_DIR = os.path.join(ROOT_DIR, PACKAGE_NAME)
COVERAGE_DIR = os.path.join(ROOT_DIR, "coverage")

# Locations of data directories for the ci package.
DATA = pkg_resources.resource_filename("ci", "data")

# Locations of documentation directories.
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
DOCS_SOURCE_DIR = os.path.join(DOCS_DIR, "source")
DOCS_API_SOURCE_DIR = os.path.join(DOCS_SOURCE_DIR, "api")
DOCS_BUILD_DIR = os.path.join(DOCS_DIR, "build")

# Templates for environment names.
ENVIRONMENT_TEMPLATE = "{prefix}-{python_version}-{toolkit}"

# EDM configuration file.
EDM_CONFIGURATION = os.path.join(DATA, "edm.yml")

# Mapping from example names to script filenames.
EXAMPLES = {
    "squares": "slow_squares.py",
    "pi": "pi_iterations.py",
    "primes": "prime_counting.py",
}

# Python runtime versions.
RUNTIME_VERSION = {
    PYTHON36: "3.6",
}

# Directories and files that should be checked for flake8-cleanness.
FLAKE8_TARGETS = [
    "ci",
    "docs",
    "setup.py",
    PACKAGE_NAME,
    "examples",
]

# Platforms and Python versions that we support.
# Triples (edm-platform-string, Python major.minor version, GUI toolkit)
PLATFORMS = [
    (MACOS, PYTHON36, NULL),
    (LINUX, PYTHON36, NULL),
    (WINDOWS, PYTHON36, NULL),
    (MACOS, PYTHON36, PYQT),
    (LINUX, PYTHON36, PYQT),
    (WINDOWS, PYTHON36, PYQT),
    (MACOS, PYTHON36, PYQT5),
    (LINUX, PYTHON36, PYQT5),
    (WINDOWS, PYTHON36, PYQT5),
    (MACOS, PYTHON36, PYSIDE2),
    (LINUX, PYTHON36, PYSIDE2),
    (WINDOWS, PYTHON36, PYSIDE2),
    (MACOS, PYTHON36, WXPYTHON),
    (LINUX, PYTHON36, WXPYTHON),
    (WINDOWS, PYTHON36, WXPYTHON),
]

# Dependencies needed for all platforms, toolkits and Python versions.
CORE_DEPS = [
    "pyface",
    "setuptools",
    "traits",
]

# Python-version-specific core dependencies. Dictionary mapping Python version
# to list of requirements.
VERSION_CORE_DEPS = {}

# Additional packages needed for running tests under CI.
ADDITIONAL_CI_DEPS = [
    "flake8",
    "flake8_ets",
    "flake8_import_order",
    "pip",
]

# Toolkit-specific ci dependencies. Dictionary mapping toolkit to
# list of requirements.
TOOLKIT_CI_DEPS = {
    PYQT: ["pyqt", "traitsui"],
    PYQT5: ["pyqt5", "traitsui"],
    PYSIDE2: ["pyside2", "traitsui"],
    # wxPython is not yet available through EDM, and needs special
    # handling in the main script.
    WXPYTHON: ["traitsui"],
}

# Additional packages needed for local development, examples.
ADDITIONAL_DEVELOP_DEPS = [
    "chaco",
    "coverage",
    "enable",
    "enthought_sphinx_theme",
    "numpy",
    "sphinx",
    "traitsui",
]


def core_dependencies(python_version, toolkit):
    """
    Compute core dependencies for the Python version and toolkit.
    """
    # Make a copy to avoid accidentally mutating the CORE_DEPS global.
    dependencies = list(CORE_DEPS)
    dependencies.extend(VERSION_CORE_DEPS.get(python_version, []))
    return dependencies


def ci_dependencies(python_version, toolkit):
    """
    Return dependencies for CI
    """
    dependencies = core_dependencies(python_version, toolkit)
    dependencies.extend(ADDITIONAL_CI_DEPS)
    dependencies.extend(TOOLKIT_CI_DEPS.get(toolkit, []))
    return dependencies


def develop_dependencies(python_version, toolkit):
    """
    Return dependencies for development.
    """
    dependencies = ci_dependencies(python_version, toolkit)
    dependencies.extend(ADDITIONAL_DEVELOP_DEPS)
    return dependencies
