# (C) Copyright 2018 Enthought, Inc., Austin, TX
# All rights reserved.
#
# The code in the ci/ package is proprietary and should not be redistributed
# without explicit approval.

import os

import pkg_resources

# Main package name, used for installing development sources
# and as a flake8 target.
PACKAGE_NAME = 'traits_futures'

# Prefix used for generated bundle files and EDM environments.
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
TOOLKITS = [PYSIDE, PYQT]

# Default Python version and toolkit.
DEFAULT_PYTHON = PYTHON36
DEFAULT_TOOLKIT = PYQT

# Location of repository root. Assumes that the ci script is being
# run from the root of the repository.
ROOT_DIR = os.path.abspath('.')
PACKAGE_DIR = os.path.join(ROOT_DIR, PACKAGE_NAME)

# Locations of data directories for the ci package.
BUNDLE = pkg_resources.resource_filename('ci', 'bundle')
DATA = pkg_resources.resource_filename('ci', 'data')
SCRIPTS = pkg_resources.resource_filename('ci', 'scripts')

# Locations of documentation directories.
DOCS_DIR = os.path.join(ROOT_DIR, 'docs')
DOCS_SOURCE_DIR = os.path.join(DOCS_DIR, 'source')
DOCS_API_SOURCE_DIR = os.path.join(DOCS_SOURCE_DIR, 'api')
DOCS_BUILD_DIR = os.path.join(DOCS_DIR, 'build')

# Templates for bundle and environment names.
BUNDLE_TEMPLATE = "{prefix}-{python_version}-{toolkit}-{platform}.json"
ENVIRONMENT_TEMPLATE = "{prefix}-{python_version}-{toolkit}"

# EDM configuration file.
EDM_CONFIGURATION = os.path.join(DATA, 'edm.yml')
EDM_BUNDLEGEN_CONFIGURATION = os.path.join(DATA, 'bundle_edm.yml')

# Mapping from example names to script filenames.
EXAMPLES = {
    'squares': 'slow_squares.py',
    'pi': 'pi_iterations.py',
    'primes': 'prime_counting.py',
}

# Python runtime versions.
RUNTIME_VERSION = {
    PYTHON27: "2.7.13",
    PYTHON35: "3.5.2",
    PYTHON36: "3.6.0",
}

# Directories and files that should be checked for flake8-cleanness.
FLAKE8_TARGETS = [
    'ci',
    'setup.py',
    PACKAGE_NAME,
    'examples',
]

# Platforms and Python versions that we support.
# Triples (edm-platform-string, Python major.minor version, GUI toolkit)
PLATFORMS = [
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

# Dependencies used for bundle generation. As a general rule, anything
# that a package directly imports from should be listed here (even if it's
# already a dependency of something else listed).

# Common dependencies.
CORE_DEPS = [
    'coverage',
    'flake8',
    'mock',  # used by the pyface GuiTestAssistant
    'pip',
    'setuptools',
    'six',
    'sphinx',
    'traits',
    'traitsui',
]

# Python-version-specific core dependencies. Dictionary mapping Python version
# to list of requirements.
VERSION_CORE_DEPS = {
    PYTHON27: ['futures'],
}

# Toolkit-specific core dependencies. Dictionary mapping toolkit to
# list of requirements.
TOOLKIT_CORE_DEPS = {
    PYQT: ["pyqt"],
    PYSIDE: ["pyside"],
}

# Additional platform-specific core dependencies.
PLATFORM_CORE_DEPS = {}
