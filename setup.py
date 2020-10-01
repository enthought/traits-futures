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

from setuptools import find_packages, setup


def get_version_info():
    """ Extract version information as a dictionary from version.py. """
    version_info = {}
    version_filename = os.path.join("traits_futures", "version.py")
    with open(version_filename, "r", encoding="utf-8") as version_module:
        version_code = compile(version_module.read(), "version.py", "exec")
        exec(version_code, version_info)
    return version_info


def get_long_description():
    """ Read long description from README.rst. """
    with open("README.rst", "r", encoding="utf-8") as readme:
        return readme.read()


install_requires = [
    "pyface",
    "setuptools",
    "traits",
]


setup(
    name="traits_futures",
    version=get_version_info()["version"],
    author="Enthought",
    author_email="info@enthought.com",
    url="https://github.com/enthought/traits-futures",
    description="Patterns for reactive background tasks",
    long_description=get_long_description(),
    long_description_content_type="text/x-rst",
    keywords="background concurrency futures gui traits traitsui",
    install_requires=install_requires,
    packages=find_packages(exclude=["ci"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={
        "traits_futures.toolkits": [
            "null = traits_futures.null.init:toolkit_object",
            "qt4 = traits_futures.qt.init:toolkit_object",
            "qt = traits_futures.qt.init:toolkit_object",
        ],
    },
    python_requires=">=3.5",
    license="BSD",
)
