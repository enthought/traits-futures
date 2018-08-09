# (C) Copyright 2018 Enthought, Inc., Austin, TX
# All rights reserved.
#
# The code in the ci/ package is proprietary and should not be redistributed
# without explicit approval.
from __future__ import absolute_import, print_function, unicode_literals

import os

import pkg_resources

# Main package name, used for installing development sources
# and as a flake8 target.
PACKAGE_NAME = "traits_futures"

# Prefix used for generated EDM environments.
PREFIX = PACKAGE_NAME.lower().replace("_", "-")

# Platforms
MACOS = "osx-x86_64"
LINUX = "rh6-x86_64"
WINDOWS = "win-x86_64"

# Python versions
PYTHON27 = "py27"
PYTHON35 = "py35"
PYTHON36 = "py36"
PYTHON_VERSIONS = [PYTHON27, PYTHON35, PYTHON36]

# Toolkits
PYSIDE = "pyside"  # Qt 4, PySide 1; only available for Python 2.x.
PYQT = "pyqt"  # Qt 4, PyQt, available for Python 2 and Python 3.
WXPYTHON = "wxpython"  # available for Python 2 only.
TOOLKITS = [PYSIDE, PYQT, WXPYTHON]

# Default Python version and toolkit.
DEFAULT_PYTHON = PYTHON36
DEFAULT_TOOLKIT = PYQT

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
    PYTHON27: "2.7.13",
    PYTHON35: "3.5.2",
    PYTHON36: "3.6.0",
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
    (MACOS, PYTHON27, WXPYTHON),
    (LINUX, PYTHON27, WXPYTHON),
    (WINDOWS, PYTHON27, WXPYTHON),
    (MACOS, PYTHON27, PYSIDE),
    (LINUX, PYTHON27, PYSIDE),
    (WINDOWS, PYTHON27, PYSIDE),
    (MACOS, PYTHON27, PYQT),
    (LINUX, PYTHON27, PYQT),
    (WINDOWS, PYTHON27, PYQT),
    (MACOS, PYTHON35, PYQT),
    (LINUX, PYTHON35, PYQT),
    (WINDOWS, PYTHON35, PYQT),
    (MACOS, PYTHON36, PYQT),
    (LINUX, PYTHON36, PYQT),
    (WINDOWS, PYTHON36, PYQT),
]

# Dependencies needed for all platforms, toolkits and Python versions.
CORE_DEPS = [
    # Actual library runtime dependencies. Also need "futures" on Python 2.7.
    "pyface",
    "setuptools",
    "six",
    "traits",

    # Packages used for testing, documentation building, examples, etc.
    "chaco",
    "coverage",
    "enable",
    "flake8",
    "mock",
    "numpy",
    "pip",
    "sphinx",
    "traitsui",
]

# Python-version-specific core dependencies. Dictionary mapping Python version
# to list of requirements.
VERSION_CORE_DEPS = {
    PYTHON27: ["futures"],
}

# Toolkit-specific core dependencies. Dictionary mapping toolkit to
# list of requirements.
TOOLKIT_CORE_DEPS = {
    PYQT: ["pyqt"],
    PYSIDE: ["pyside"],
    WXPYTHON: ["wxpython"],
}
