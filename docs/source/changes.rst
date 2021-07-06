..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!


Release 0.3.0
-------------

Release date: XXXX-XX-XX

Backwards-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following backwards-incompatible changes may affect advanced users
of Traits Futures.

* The ``send`` callable passed to the background task now expects a single
  Python object as an argument, rather than accepting a message type and
  a message argument as separate arguments. Existing uses of the form
  ``send(message_type, message_args)`` will need to be changed to
  ``send((message_type, message_args))``. This affects those writing their
  own background task types, but does not affect users of the existing
  background task types.
* The ``state`` trait of the ``~.TraitsExecutor`` is now read-only;
  previously, it was writable.

Other Changes
~~~~~~~~~~~~~

* Traits Futures now requires Traits 6.2.0 or later.
* Python 3.5 is no longer supported. Traits Futures requires Python 3.6
  or later.


Release 0.2.0
-------------

Release date: 2020-09-24

This is a feature release of Traits Futures. The main features of this
release are:

* Improved support for user-defined background task types.
* Easier creation of background calculations that can be (cooperatively)
  cancelled mid-calculation.
* Significant internal refactoring and cleanup, aimed at eventual support
  for alternative front ends (GUI event loops other than the Qt event
  loop) and back ends (e.g., multiprocessing).
* Improved and expanded documentation.

There are no immediately API-breaking changes in this release: existing working
code using Traits Futures 0.1.1 should continue to work with no changes
required. However, some parts of the existing API have been deprecated, and
will be removed in a future release. See the Changes section below for more
details.

Detailed changes follow. Note that the list below is not exhaustive: many
more minor PRs have been omitted.

Features
~~~~~~~~

* Users can now easily create their own background task types to supplement
  the provided task types (background calls, background iterations and
  background progress). A combination of a new :class:`~.ITaskSpecification`
  interface and a convenience :class:`~.BaseFuture` base class support this.
  (#198)
* The :func:`~.submit_iteration` function now supports generator functions that
  return a result. This provides an easy way to submit background computations
  that can be cancelled mid-calculation. (#167)
* The :class:`~.TraitsExecutor` class now accepts a ``max_workers`` argument,
  which specifies the maximum number of workers for a worker pool created
  by the executor. (#125)
* There are new task submission functions :func:`~.submit_call`,
  :func:`~.submit_iteration` and :func:`~.submit_progress`. These functions
  replace the eponymous existing :class:`~.TraitsExecutor` methods, which are
  now deprecated. (#166)
* There's a new :class:`~.IFuture` interface class in the
  :mod:`traits_futures.api` module, to aid in typing and Trait declarations.
  (#169)
* A new :class:`~.IParallelContext` interface supports eventual addition
  of alternative back ends. The new :class:`~.MultithreadingContext` class
  implements this interface and provides the default threading back-end.
  (#149)

Changes
~~~~~~~

* The ``state`` trait of :class:`~.CallFuture`, :class:`~.IterationFuture` and
  :class:`~.ProgressFuture` used to be writable. It's now a read-only property
  that reflects the internal state. (#163)
* The default number of workers in an owned worker pool (that is, a worker pool
  created by a :class:`~.TraitsExecutor`) has changed. Previously it was
  hard-coded as ``4``. Now it defaults to whatever Python's
  :mod:`concurrent.futures` executors give, but can be controlled by passing
  the ``max_workers`` argument. (#125)
* The ``submit_call``, ``submit_iteration`` and ``submit_progress``
  methods on the :class:`~.TraitsExecutor` have been deprecated. Use the
  :func:`~.submit_call`, :func:`~.submit_iteration` and
  :func:`~.submit_progress` convenience functions instead. (#159)
* The ``thread_pool`` argument to :class:`~.TraitsExecutor` has been renamed
  to ``worker_pool``. The original name is still available for backwards
  compatibility, but its use is deprecated. (#144, #148)
* Python 2.7 is no longer supported. Traits Futures requires Python >= 3.5,
  and has been tested with Python 3.5 through Python 3.9. (#123, #130, #131,
  #132, #133, #138, #145)

Fixes
~~~~~

* Don't create a new message router at executor shutdown time. (#187)

Tests
~~~~~

* Fix some intermittent test failures due to test interactions. (#176)
* The 'null' backend that's used for testing in the absence of a Qt backend
  now uses a :mod:`asyncio`-based event loop instead of a custom event loop.
  (#107, #179)
* Rewrite the Qt ``GuiTestAssistant`` to react rather than polling. This
  significantly speeds up the test run. (#153)
* Ensure that all tests properly stop the executors they create. (#108, #146)
* Refactor the test structure in preparation for multiprocessing
  support. (#135, #141)
* Test the ``GuiTestAssistant`` class. (#109)

Developer tooling
~~~~~~~~~~~~~~~~~

* Add a new ``python -m ci shell`` click cmd. (#204)
* Update edm version in CI. (#205)
* Add checks for missing or malformed copyright headers in Python files (and
  fix existing copyright headers). (#193)
* Add import order checks (and fix existing import order bugs). (#161)
* Add separate "build" and "ci" modes for setting up the development
  environment. (#104)
* Don't pin dependent packages in the build environment. (#99)

Documentation
~~~~~~~~~~~~~

* Update docs to use the Enthought Sphinx Theme. (#128)
* Autogenerated API documentation is now included in the documentation
  build. (#177, #181)
* Restructure the documentation to avoid nesting 'User Guide'
  under 'User Documentation'. (#191)
* Document creation of new background task types. (#198)
* Document use of :func:`~.submit_iteration` for interruptible tasks. (#188)


Release 0.1.1
-------------

Release date: 2019-02-05

This is a bugfix release, in preparation for the first public release to PyPI.
There are no functional or API changes to the core library since 0.1.0 in this
release.

Fixes
~~~~~

- Add missing ``long_description`` field in setup script. (#116, backported
  in #118)

Changes
~~~~~~~

- Add copyright headers to all Python and reST files. (#114, backported in
  #118)

Build
~~~~~

- Remove unnecessary bundle generation machinery. (#99, backported in #118)


Release 0.1.0
-------------

Release date: 2018-08-08

Initial release. Provides support for submitting background calls, iterations,
and progress-reporting tasks for Traits UI applications based on Qt.
