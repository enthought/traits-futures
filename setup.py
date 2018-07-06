from setuptools import find_packages, setup


setup(
    name='traits-futures',
    version=0.1,
    author="Enthought",
    description="Patterns for reactive background tasks",
    install_requires=['traits', 'six'],
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
)
