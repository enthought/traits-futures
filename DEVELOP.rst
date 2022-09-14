..
   (C) Copyright 2018-2022 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!


Traits Futures: for developers
==============================

These instructions are aimed at developers working with Traits Futures.

Getting started
---------------

You'll need a Python 3 environment for development. Any environment using
Python >= 3.7 will do. For example, you could create and activate a new venv
using something like::

    python3.10 -m venv ../traits-futures && source ../traits-futures/bin/activate

Adjust the venv name and location to your taste.

To install the package into the current environment, in editable mode, do::

    pip install -e .

To run tests, do::

    python -m unittest

To run a style check::

    python -m pip install ".[style]"
    python -m flake8
    python -m isort . --check --diff
    python -m black . --check --diff

To build the documentation::

    python -m pip install -r docs/requirements.txt
    cd docs
    python -m sphinx -b html -d doctrees source build
