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

Release date: 2021-07-XX

Features
~~~~~~~~

* Multiprocessing support: the :class:`~.TraitsExecutor` can now submit
  background tasks to a process pool instead of a thread pool. Since this
  support has not yet been tested in the wild, this support should be
  considered provisional for now - the API and the capabilities may change in a
  future release. Feedback is welcome!
* wxPython support: Traits Futures now supports the wxPython event loop as well
  as Qt-based toolkits.
* asyncio support: the executor can make use of an asyncio event loop in place
  of a GUI toolkit event loop. This is potentially useful in unit tests, and
  when running headless.
* Improved shutdown: there's a new :meth:`~.TraitsExecutor.shutdown` method,
  suitable for use at process exit time, or in unit tests. This method is
  blocking: it waits for tasks created by the executor to completed, and then
  shuts down all resources associated with the executor.
* Improved logging: there's now debug-level logging of key state changes
  and interactions, to aid in post-mortem debugging.

Changes
~~~~~~~

* The ``cancel`` method of a future no longer raises :exc:`RuntimeError` when a
  future is not cancellable. If a task has already completed, or has previously
  been cancelled, calling ``cancel`` on the associated future does not change
  the state of the future, and the call returns ``False``. Otherwise it changes
  the future's state to ``CANCELLING``, requests cancellation of the associated
  task, and returns ``True``.
* The ``state`` trait of the ``~.TraitsExecutor`` is now read-only;
  previously, it was writable.
* The ``executor`` and ``callable`` arguments to the ``submit_call``,
  ``submit_iteration`` and ``submit_progress`` convenience functions should
  be considered positional-only, and should not be passed by name. This
  restriction may be enforced in a future version of the library.
* The string representation of the exception type created by
  ``marshal_exception`` has been simplified: instead of appearing in the form
  ``"<class 'traits.trait_errors.TraitError'>"``, it has the form
  ``"traits.trait_errors.TraitError"``.
* Tasks may now only be submitted to a ``~.TraitsExecutor`` on the main thread.
* The ``traits_futures.toolkits`` setuptools entry point group used for
  supplying custom toolkit support has been renamed to
  ``traits_futures.event_loops``.
* There are a number of backwards-incompatible changes to the machinery used
  for creating custom task types and futures. The API for creating custom
  task types should be considered provisional: it may change in future
  releases. Notable changes include:

  * A new ``BaseTask`` abstract base class, which can be subclassed to create
    custom background tasks. Those background tasks should override the
    ``run`` method, which takes no arguments. The ``BaseTask`` provides
    ``send`` and ``cancelled`` methods to send messages to the associated
    future, and to check for cancellation requests.
  * The ``ITaskSpecification.background_task`` method has been renamed to
    ``task``.
  * The ``ITaskSpecification.future`` method now requires a cancellation callback
    to be passed.
  * The ``IFuture`` interface has a new ``receive`` method which receives
    messages from the background task.
  * The ``IFuture`` interface is much smaller, containing only the ``receive``
    and ``cancel`` methods.
  * The ``BaseFuture`` has a new ``dispatch`` public method, which can be
    overridden in subclasses in order to customize the dispatch of messages
    received from the associated task. The default implementation dispatches to
    methods named ``_process_<msgtype>``, as before.

  See the documentation for more details on how to create custom task types.

Fixes
~~~~~

* The message routing machinery will no longer block indefinitely in the
  (hypothetical) event that no message exists to be retrieved on the message
  queue. Instead, it will fail fast with a ``QueueError`` exception. This
  situation should never happen in normal use; please report it if you ever
  witness it.
* The ``ProgressCancelled`` exception used by the background task submitted
  via ``submit_progress`` is now public, in case that task needs to catch
  the exception.
* The marshal_exception function has been fixed not to rely on the global
  ``sys.exception_info`` state.
* A bogus "message" trait that never did anything has been removed from
  ``IFuture``.
* The cancellation callback supplied to a ``BaseFuture`` instance is now always
  cleared when the future completes. Previously the ``BaseFuture`` object
  would sometimes hold onto the reference to the cancellation callback.

Continuous integration and build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The default GitHub branch has been renamed from "master" to "main".
* Continuous integration has been migrated from Travis CI and Appveyor
  to GitHub Actions. The per-commit tests are run on Linux and Windows, on
  Python 3.6 and Python 3.8. There are several GitHub Actions workflows in
  addition to the normal CI testing workflow (``run-tests.yml``):

  * The ``build-docs.yml`` workflow provides automated documentation builds
    deployed to https://docs.enthought.com/traits-futures/dev/index.html on
    each PR merge to the main branch.
  * The ``publish-on-pypi.yml`` workflow automatically uploads a wheel and
    sdist to PyPI when a GitHub release is created.
  * The ``test-docs.yml`` workflow performs a nitpicky documentation build
    check on each commit to an open PR.
  * The ``check-style.yml`` workflow performs style checks are using ``black``,
    ``isort``, ``flake8`` and ``flake8-ets`` on each commit to an open PR.
  * The ``weekly-scheduled-tests.yml`` workflow runs comprehensive tests on
    a weekly basis, and reports success or failure back to a relevant Enthought
    Slack channel.

* The ``ci`` tool now supports ``-h`` for getting help.
* Tests are always run under ``faulthandler``.
* Example files are now included in the various style checks.

Packaging changes
~~~~~~~~~~~~~~~~~

* Python 3.6 or later is now required.
* Traits 6.2 or later is now required.
* ``setuptools`` is no longer a runtime dependency.
* The ``setup`` file now declares ``extras_require`` for additional
  dependencies such as ``docs``, ``pyqt5`` and ``pyside2``.

Test suite
~~~~~~~~~~

* The test suite now uses the ``asyncio`` event loop for the majority of
  its tests. It uses the Qt or Wx event loop only for tests specific to
  those toolkits.

Documentation
~~~~~~~~~~~~~

* New "overview" documentation section explaining why Traits Futures exists
  and what problems it solves.
* New documentation section on testing code that uses Traits Futures.
* A "Read the Docs" configuration file has been added.
* The changelog is now maintained as part of the documentation.
* All examples are now part of the documentation.
* All example scripts are downloadable from the documentation.
* All examples now use the new ``observe`` machinery instead of
  ``on_trait_change``.
* The ``sphinx-apidoc`` autogeneration step is now run automatically as
  part of the normal Sphinx build.
* Sphinx 3.5 or later is now required to build the documentation.
* Development information has been removed from ``README.rst``, and moved into
  a separate ``DEVELOP.rst`` file.
* Various Sphinx warnings from a combination of napoleon and autodoc have been
  fixed, and the documentation now builds cleanly in "nitpicky" mode.
* The example scripts displayed directly in the documentation no longer
  include the copyright headers.
* The autodoc templates are no longer missing a newline at EOF.
* The ``pi_iterations`` example has been fixed to give correct counts.
  Previously it was giving incorrect results as a result of NumPy integer
  overflow.


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
