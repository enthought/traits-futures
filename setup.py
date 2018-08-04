import os
import sys

from setuptools import find_packages, setup


def get_version_info():
    """ Extract version information as a dictionary from version.py. """
    version_info = {}
    version_filename = os.path.join("traits_futures", "version.py")
    with open(version_filename, 'r') as version_module:
        version_code = compile(version_module.read(), "version.py", 'exec')
        exec(version_code, version_info)
    return version_info


version = get_version_info()['version']

install_requires = [
    'pyface',
    'setuptools',
    'six',
    'traits',
    'traitsui',
]
if sys.version_info < (3,):
    install_requires.append('futures')

setup(
    name='traits-futures',
    version=version,
    author="Enthought",
    description="Patterns for reactive background tasks",
    install_requires=install_requires,
    packages=find_packages(exclude=["ci"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    entry_points={
        'traits_futures.routers': [
            'qt4 = traits_futures.qt.message_router:MessageRouter',
            'qt = traits_futures.qt.message_router:MessageRouter',
        ],
    },
)
