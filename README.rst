Traits Futures
--------------

The **traits_futures** package demonstrates robust design patterns for reactive
background jobs triggered from a TraitsUI application.

Motivating example
------------------
A customer has asked you to wrap their black-box optimization code in a GUI.

You build a simple TraitsUI GUI that allows the user to set inputs and options
and then press the big green "Calculate" button. The requirements look
something like this:

- The UI should remain usable and responsive while the background calculation
  is running.
- The UI should update (e.g., show a plot, or show results) in response to the
  background calculation completing normally.
- The background job should be cancellable.
- The UI should react appropriately if the background job raises an exception.

And there are some further ease-of-development requirements:

- As far as possible, the UI developer shouldn't have to think about managing
  the background threads or re-dispatching incoming information from the
  background task(s). The UI developer should be able to simply listen to and
  react to suitable traits for information coming in from the background task.
- It should be possible to switch between using background threads and
  background process (and possibly also coroutines) with minimal effort.

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

    python -m ci flake8

To build the documentation::

    python -m ci doc

The example scripts can be run with::

    python -m ci example <example-name>

Run ``python -m ci example`` to see the list of available examples.

All of the above commands take two options. The ``--python-version`` option
lets you specify the Python version to use for the development environment. The
``--toolkit`` option allows you to choose between using PyQt and PySide on
Python 2. Run ``python -m ci <command> --help`` for more information on any
of these commands.
