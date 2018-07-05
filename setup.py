from setuptools import find_packages, setup


setup(
    name='traits-futures',
    version=0.1,
    author="Enthought",
    description="Patterns for reactive background tasks",
    install_requires=['traits', 'six'],
    packages=find_packages(exclude=["ci"]),
)
