..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!


Release 0.4.0
-------------

Release date: XXXX-XX-XX


Continuous integration and build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add cron-job-based workflow to validate installation of the latest
  wheel and sdist from PyPI. (#465)
* Add new script for automating gh-pages updates, and extend automated
  documentation building to the maintenance branches in addition to
  the main branch. (#474)


Release 0.3.1
-------------

Release date: 2021-07-30

This is a bugfix release that fixes a regression introduced in version 0.3.0.

Fixes
~~~~~

* Fix regression where |BaseFuture| subclasses could not be instantiated
  without any arguments. (#467)


Release 0.3.0
-------------

Release date: 2021-07-29

Summary
~~~~~~~

This is a feature release of Traits Futures, with a some minor backwards
incompatible changes that users should be aware of. New features include
multiprocessing support, wxPython support, support for delivering events using
an |asyncio| event loop in place of a GUI toolkit event loop, and better
support for synchronous executor shutdown.

Migration guide
~~~~~~~~~~~~~~~

The majority of existing code using Traits Futures 0.2.0 should continue to
work with Traits Futures 0.3.0 with no changes. However, there are some minor
changes that could affect current code, and some major backwards-incompatible
changes for anyone making use of the |ITaskSpecification| interface to create
their own background task types. For the |ITaskSpecification| changes, see
the detailed PR-by-PR change list below.

* The |cancel| method on a future no longer raise a |RuntimeError| exception
  when a future is not cancellable; instead, it silently does nothing. Code
  that needs to distinguish can use the new return value of the |cancel| method
  to determine whether the |cancel| call actually caused cancellation to occur.
  Code that currently checks the |cancellable| property before cancelling
  should be able to safely drop that check.
* The |executor_state| trait of a |TraitsExecutor| is no longer writable.
* The ``executor`` and ``callable`` parameters to the |submit_call|,
  |submit_iteration| and |submit_progress| functions may become
  positional-only in a future version of Traits Futures. If you're passing
  arguments by name instead of by position, for example using
  ``submit_call(executor=my_executor, callable=do_calculation, ...)``, you
  should fix your code to pass by position instead: ``submit_call(my_executor,
  do_calculation, ...)``.

Features
~~~~~~~~

* Multiprocessing support: the |TraitsExecutor| can now submit
  background tasks to a process pool instead of a thread pool. Since this
  support has not yet been tested in the wild, this support should be
  considered provisional for now - the API and the capabilities may change in a
  future release. Feedback is welcome! (#387, #173, #284, #283)
* wxPython support: Traits Futures now supports the wxPython event loop as well
  as Qt-based toolkits. (#269, #256, #246)
* asyncio support: the executor can make use of an asyncio event loop in place
  of a GUI toolkit event loop. This is potentially useful in unit tests, and
  when running headless. (#314, #322)
* Improved shutdown: there's a new |shutdown| method,
  suitable for use at process exit time, or in unit tests. This method is
  blocking: it waits for tasks created by the executor to completed, and then
  shuts down all resources associated with the executor. (#419, #395, #380,
  #378, #334)
* Improved logging: there's now debug-level logging of key state changes
  and interactions, to aid in post-mortem debugging. (#296, #293)

Changes
~~~~~~~

* The |cancel| method of a future no longer raises |RuntimeError| when a
  future is not cancellable. If a task has already completed, or has previously
  been cancelled, calling |cancel| on the associated future does not change
  the state of the future, and the call returns ``False``. Otherwise it changes
  the future's state to |CANCELLING|, requests cancellation of the associated
  task, and returns ``True``. (#420)
* The |executor_state| trait of the |TraitsExecutor| is now read-only;
  previously, it was writable. (#344)
* The ``executor`` and ``callable`` arguments to the |submit_call|,
  |submit_iteration| and |submit_progress| convenience functions should
  be considered positional-only, and should not be passed by name. This
  restriction may be enforced in a future version of the library. (#409)
* The string representation of the exception type created by
  |marshal_exception| has been simplified: instead of appearing in the form
  ``"<class 'traits.trait_errors.TraitError'>"``, it has the form
  ``"traits.trait_errors.TraitError"``. (#391)
* Tasks may now only be submitted to a |TraitsExecutor| on the main thread.
  An attempt to submit a task from a thread other than the main thread will
  raise |RuntimeError|. (#305)
* There are a number of backwards-incompatible changes to the machinery used
  for creating custom task types and futures. The API for creating custom
  task types should be considered provisional: it may change in future
  releases. Notable changes include:

  * A new |BaseTask| abstract base class, which can be subclassed to create
    custom background tasks. Those background tasks should override the
    |run| method, which takes no arguments. The |BaseTask| provides
    |send| and |cancelled| methods to send messages to the associated
    future, and to check for cancellation requests. (#435, #426)
  * The ``ITaskSpecification.background_task`` method has been renamed to
    |task|. (#425)
  * The |future| method now requires a cancellation callback to be passed.
    (#414)
  * The |IFuture| interface has a new |receive| method which receives
    messages from the background task. (#396)
  * The |IFuture| interface is much smaller, containing only the |receive|
    and |cancel| methods. (#431, #436, #428)
  * The |BaseFuture| has a new |dispatch| public method, which can be
    overridden in subclasses in order to customize the dispatch of messages
    received from the associated task. The default implementation dispatches to
    methods named ``_process_<msgtype>``, as before. (#427)

  See the documentation for more details on how to create custom task types.
* The ``traits_futures.toolkits`` setuptools entry point group used for
  supplying custom toolkit support has been renamed to
  ``traits_futures.event_loops``. The old "toolkit"-based names have been
  converted to "event-loop"-based names throughout. (#312, #365)
* The toolkit / event-loop contribution machinery has been significantly
  reworked. The interface for contributing new event loops is currently
  undocumented and should be considered experimental: the API may change in
  future releases. (#298, #300)


Fixes
~~~~~

* The message routing machinery will no longer block indefinitely in the
  (hypothetical) event that no message exists to be retrieved on the message
  queue. Instead, it will fail fast with a |queue.Empty| exception. This
  situation should never happen in normal use; please report it if you ever
  witness it. (#413)
* The |TaskCancelled| exception used by the background task submitted
  via |submit_progress| is now public and exposed in |traits_futures.api|, in
  case that task needs to catch the exception. (#449, #317)
* The |marshal_exception| function has been fixed not to rely on the global
  |sys.exc_info| state. (#390)
* A spurious "message" trait that never did anything has been removed from
  |IFuture|. (#394)
* The cancellation callback supplied to a |BaseFuture| instance is now always
  cleared when the future completes. Previously the |BaseFuture| object
  would sometimes hold onto the reference to the cancellation callback. (#389)

Continuous integration and build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The default GitHub branch has been renamed from "master" to "main". (#277)
* Continuous integration has been migrated to GitHub Actions. The per-commit
  tests are run on Linux and Windows, on Python 3.6 and Python 3.8. There are
  several GitHub Actions workflows:

  * The ``run-tests.yml`` workflow runs the test suite on each commit to
    an open PR. (#237)
  * The ``check-style.yml`` workflow performs style checks are using ``black``,
    ``isort``, ``flake8`` and ``flake8-ets`` on each commit to an open PR.
    (#416, #266)
  * The ``test-docs.yml`` workflow performs a nitpicky documentation build
    check on each commit to an open PR. (#265)
  * The ``build-docs.yml`` workflow provides automated documentation builds
    deployed to https://docs.enthought.com/traits-futures/dev/index.html on
    each PR merge to the main branch. (#257, #262, #264, #259)
  * The ``publish-on-pypi.yml`` workflow automatically uploads a wheel and
    sdist to PyPI when a GitHub release is created. (#439)
  * The ``weekly-scheduled-tests.yml`` workflow runs comprehensive tests on
    a weekly basis, and reports success or failure back to a relevant Enthought
    Slack channel. (#410, #303, #297)

* Travis CI and Appveyor configurations have been removed. (#270, #267)
* CI runs for Qt now use PySide2 in preference to PyQt5. (#233)
* Style checks now use ``isort`` rather than ``flake8-import-order``. (#285)
* Copyright headers are now checked using the ``flake8-ets`` package instead
  of local custom code. (#234)
* Tests are always run under ``faulthandler``. (#337)
* All example scripts except one are now subject to style checking. (#374,
  #287)
* The ``ci`` tool now supports ``-h`` for getting help. (#235)
* The ``ci`` tool now uses the EDM executable instead of the batch file on
  Windows, preventing mangling of version modifiers on package requirements.
  (#247)
* Miscellanous minor build changes and fixes. (#408, #368, #279)


Packaging changes
~~~~~~~~~~~~~~~~~

* Python 3.6 or later is now required. (#239)
* Python 3.10 is now supported. (#454)
* Traits 6.2 or later is now required. (#373)
* The ``setuptools`` package is no longer a runtime dependency. (#240)
* The ``setup`` file now declares ``extras_require`` for additional
  dependencies such as ``docs``, ``pyqt5`` and ``pyside2``. (#451)

Tests
~~~~~

* The test suite now uses the |asyncio| event loop for the majority of
  its tests. It uses the Qt or Wx event loop only for tests specific to
  those toolkits. (#321, #319, #315)
* Most tests now use the new |shutdown| method for executor shutdown. (#386)
* The ``GuiTestAssistant`` has been renamed to |TestAssistant|, to avoid
  confusion with Pyface's ``GuiTestAssistant``. This class is not yet part
  of the Traits Futures API, and users should avoid depending on it. (#388)
* The |TestAssistant| is no longer toolkit-specific; the toolkit-specific
  component has been pulled into a new |IEventLoopHelper| interface, with
  implementations of that interface for each supported toolkit. (#307)
* New |exercise_event_loop| method on the |TestAssistant|. (#377)
* Improve testing for the case of an externally-supplied worker pool. (#343)

Documentation
~~~~~~~~~~~~~

* New "overview" documentation section explaining why Traits Futures exists
  and what problems it solves. (#325, #327)
* New documentation section on testing code that uses Traits Futures. (#278)
* A "Read the Docs" configuration file has been added. (#411)
* The changelog is now maintained as part of the documentation. (#447, #363,
  #350, #458)
* All examples are now part of the documentation. (#355)
* All example scripts are downloadable from the documentation. (#353)
* All examples now use the new Traits ``observe`` machinery instead of
  ``on_trait_change``. (#441, #371, #370)
* All examples have been updated to use the new |shutdown| method. (#385, #423)
* The ``sphinx-apidoc`` autogeneration step is now run automatically as
  part of the normal Sphinx build. (#348)
* Sphinx 3.5 or later is now required to build the documentation. (#357)
* Avoid using Sphinx 4.x until it has better stability. (#457)
* Development information has been removed from ``README.rst``, and moved into
  a separate ``DEVELOP.rst`` file. (#352)
* Various Sphinx warnings from a combination of napoleon and autodoc have been
  fixed, and the documentation now builds cleanly in "nitpicky" mode. (#429,
  #430, #424, #422, #400, #406, #405, #404, #403, #402, #401)
* The example scripts displayed directly in the documentation no longer
  include the copyright headers. (#326)
* The autodoc templates are no longer missing a newline at EOF. (#260)
* The ``pi_iterations`` example has been fixed to give correct counts.
  Previously it was giving incorrect results as a result of NumPy integer
  overflow. (#249)
* The ``prime_counting`` example has been fixed to avoid an occasional
  |AttributeError| under unusual timing conditions. (#450)
* Miscellaneous cleanups and minor fixes. (#421, #455, #292, #223, #221)

Internal refactoring
~~~~~~~~~~~~~~~~~~~~

* Significant internal refactoring to better decouple the toolkit
  implementation from the message routing, to decouple the future
  implementation from the executor, and to make toolkit selection easier.
  (#392, #381, #382, #364, #362, #360, #332, #331,
  #306, #282, #255, #231, #226, #227)
* Other minor fixes and non-user-facing changes. (#415, #397, #393,
  #384, #376, #372, #361, #347, #349, #346, #342, #338, #336, #335,
  #330, #323, #309, #308, #286, #276, #232, #213, #212)



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


..
   substitutions

.. |asyncio| replace:: :mod:`asyncio`
.. |AttributeError| replace:: :exc:`AttributeError`
.. |queue.Empty| replace:: :exc:`queue.Empty`
.. |RuntimeError| replace:: :exc:`RuntimeError`
.. |sys.exc_info| replace:: :func:`sys.exc_info`

.. |BaseFuture| replace:: :class:`~.BaseFuture`
.. |BaseTask| replace:: :class:`~.BaseTask`
.. |cancel| replace:: :meth:`~.BaseFuture.cancel`
.. |cancellable| replace:: :attr:`~.BaseFuture.cancellable`
.. |cancelled| replace:: :meth:`~.BaseTask.cancelled`
.. |CANCELLING| replace:: :data:`~.CANCELLING`
.. |dispatch| replace:: :meth:`~.BaseFuture.dispatch`
.. |executor_state| replace:: :attr:`~.TraitsExecutor.state`
.. |exercise_event_loop| replace:: :meth:`~.TestAssistant.exercise_event_loop`
.. |future| replace:: :meth:`~.ITaskSpecification.future`
.. |IEventLoopHelper| replace:: :class:`~.IEventLoopHelper`
.. |IFuture| replace:: :class:`~.IFuture`
.. |ITaskSpecification| replace:: :class:`~.ITaskSpecification`
.. |marshal_exception| replace:: :func:`~.marshal_exception`
.. |receive| replace:: :meth:`~.IFuture.receive`
.. |run| replace:: :meth:`~.BaseTask.run`
.. |send| replace:: :meth:`~.BaseTask.send`
.. |shutdown| replace:: :meth:`~.TraitsExecutor.shutdown`
.. |submit_call| replace:: :func:`~.submit_call`
.. |submit_iteration| replace:: :func:`~.submit_iteration`
.. |submit_progress| replace:: :func:`~.submit_progress`
.. |task| replace:: :meth:`~.ITaskSpecification.task`
.. |TaskCancelled| replace:: :exc:`~.TaskCancelled`
.. |TestAssistant| replace:: :exc:`~.TestAssistant`
.. |traits_futures.api| replace:: :mod:`traits_futures.api`
.. |TraitsExecutor| replace:: :class:`~.TraitsExecutor`
