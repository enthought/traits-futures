..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!


Traits Futures: for developers
==============================

These instructions are aimed at developers working with Traits Futures
within an EDM environment. However, note that it's not necessary to use
EDM to work on Traits Futures.

Getting started
---------------
The ``ci`` helper package in the source repository aids in setting up a
development environment and running tests and examples. It requires EDM, along
with a Python bootstrap environment equipped with ``click`` and ``setuptools``.

To create a development environment, run::

    python -m ci build

from the top-level of the repository, within the Python bootstrap environment.

To run tests for the traits_futures EDM environment, do::

    python -m ci test

To run tests under coverage::

    python -m ci coverage

To run a style check::

    python -m ci style

To build the documentation::

    python -m ci doc

The example scripts can be run with::

    python -m ci example <example-name>

Run ``python -m ci example`` to see the list of available examples.

All of the above commands take two options. The ``--python-version`` option
lets you specify the Python version to use for the development environment. The
``--toolkit`` option allows you to specify a GUI backend. Run ``python -m ci
<command> --help`` for more information on any of these commands.
