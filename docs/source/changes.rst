..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!



Continuous integration and build machinery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add workflow for uploading releases to PyPI (#439)
* Turn on nitpicky mode for documentation builds (#429)
* Add black check to the style checks (#416)
* DEV : RtD docs config (#411)
* Setup slack notifications for cron jobs (#410)
* Update CI workflows (#408)
* Set PYTHONUNBUFFERED in all workflows (#368)
* Enable faulthandler when running tests (#337)
* Rename 'master' to 'main' in the documentation build workflow (#277)
* Automate documentation build for the master branch (#257)
* Add Python 3.8 testing for cron job (#303)
* Add cron job that runs the test suite against the latest ETS source (#297)
* Replace flake8-import-order with isort (#285)
* Fix import grouping and ordering throughout the codebase (#286)
* Extend 'ci format' and 'ci style' checks to example directories (#287)
* Remove Travis and Appveyor configs and associated machinery (#270)
* Add GitHub Actions (#237)
* Add GitHub Actions workflow for style checking (#266)
* Add a per-PR workflow to test the documentation build (#265)
* Adjust runtime dependencies (#240)
  - added extras_require section
* Support -h for getting help (#235)
* DEV : Use flake8-ets package (#234)



Features
~~~~~~~~

* Finalise multiprocessing support (#173)
* Mark multiprocessing support as provisional (#387)
* Feature: executor.shutdown (#334)
* Add basic logging to the TraitsExecutor (#296)
* Adding logging for message routers (#293)
* Add wx toolkit support (#246)



Changes
~~~~~~~

* Make BaseTask easier to use (#435)
* Repurpose IFuture (#431)
* Change cancel method to never raise (#420)
* Rename ITaskSpecification.background_task to ITaskSpecification.task (#425)
* Extract public 'dispatch' method from task_sent (#427)
* Remove the blocking wait during message routing (#413)
* Document 'positional-only' arguments (#409)
* Change string representation of marshalled exception type (#391)
* ITaskSpecification change: 'send' expects a single argument (#364)
* Prevent task submission off the main thread (#305)
* Make the ProgressCancelled exception public (#317)
* Require Python 3.6 or later (#239)
* Adjust runtime dependencies (#240)
  - setuptools is no longer a runtime dependency

Fixes
~~~~~

* Fix marshal_exception not to use global state (#390)
* Remove bogus "message" trait from IFuture (#394)
* Make sure that the cancellation callback is always cleared (#389)

Test suite
~~~~~~~~~~

* Use the asyncio context by default for testing (#321)


Documentation
~~~~~~~~~~~~~

* Only exclude one troublesome example, not all of them (#374)
* Replace dynamic use of "on_trait_change" handlers with "observe" (#373)
* DEV : Replace static change handlers with observe decorated methods (#372)
* Replace "on_trait_change" decorator with "observe" decorator (#371)
* Automatically run sphinx-apidoc during documentation build (#348)
* Set 3.5 as the minimum Sphinx version (#357)
* Move examples into documentation (#355)
* Remove developer guide from README (#352)
* Make all example scripts downloadable (#353)
* Move changelog to documentation (#350)
* Flesh out last section of the overview (#327)
* Docs: add overview documentation (#325)
* Add brief documentation on testing (#278)



Documentation fixes
~~~~~~~~~~~~~~~~~~~

* Fix last of the Sphinx warnings (#430)
* Doc: Fix some bad Sphinx roles (#424)
* Clean up various references in the introduction section of the user guide (#421)
* Fix Sphinx warnings about 'callable' (#422)
* Doc: provide type aliases for common classes (#400)
* Remove unresolvable references (#406)
* Remove 'event-like' as a type (#405)
* Fix 'callable' type descriptions (#404)
* Fix ad-hoc type descriptions (#403)
* Doc: fix bad std. lib. references (#402)
* Fix descriptions coming after Parameters (#401)
* Remove copyright headers from literalincludes (#326)
* Fix appearance of copyright in documentation (#292)
* Fix autodoc templates to avoid missing newline at EOF (#260)
* Make sure we use Python ints in pi_iterations example (#249)


Internal refactoring
~~~~~~~~~~~~~~~~~~~~

Also includes outdated changes and fixes for things introduced since
0.2.0

* FIX : Migrate static _fired methods with observe decorated methods (#441)
* Move IFuture definition to i_task_specification module (#436)
* Fix 'state' trait type in IFuture (#428)
* Fix behaviour of route_until with timeout and queued messages (#419)
* Fix missing 'self' in method definition (#426)
* Remove an unused method (#423)
* More TraitsExecutor / IFuture decoupling (#414)
* Style: keep black happy (#415)
* Decouple TraitsExecutor from future implementation (#396)
* Fix bad string interpolation in shutdown log message (#395)
* Rename task classes (#397)
* Remove comment that was both redundant and out of date (#393)
* Refactor to add ABANDONED message (#392)
* Rename GuiTestAssistant to TestAssistant (#388)
* Update examples to use 'shutdown' (#385)
* Update tests to use 'shutdown', where it makes sense (#386)
* Ensure that Pingees are always collected on the main thread (#384)
* Refactor traits_executor (#381)
* Refactor to move 'progress' argument check in submit_progress (#382)
* Route messages during executor shutdown (#380)
* Feature: IMessageRouter.route_until (#378)
* Add GuiTestAssistant.exercise_event_loop (#377)
* Style fix from black (#376)
* DEV : Replace depends_on with observe for Property traits (#370)
* Rename gui_context to event_loop (#365)
* Simplify messages, ensure cleanup ordering (#362)
* Refactor: fix wrapper asymmetry (and inaccurate docstring) (#360)
* Add section for backwards-incompatible changes to the changelog (#363)
* Fix black complaint (#361)
* Fix missing 'f' prefix on what was supposed to be an f-string. (#347)
* Join a thread in a test (#349)
* Fix logging inconsistency (#346)
* Refactor executor states and shutdown (#344)
* Run the executor tests with an external worker pool (#343)
* Fix temporal coupling between Pingee and Pinger (#332)
* Fix potential race condition in long_running_task (#342)
* Make sure that long_running_task doesn't run forever (#338)
* Don't call stop on a STOPPING executor (#335)
* Fix executor tests that weren't correctly specifying the GUI context (#336)
* Move event loop to AsyncioContext (#331)
* Don't try to use a new event loop for every test (#330)
* Bump version for continued developer towards 0.3.0 (#212)
* Decouple parallelism context and GUIContext (#322)
* Re-blacken the source (#323)
* Add tests for each of the IEventLoopHelper implementations (#319)
* Add toolkit-specific Pingee tests (#315)
* Refactor: pull up ETSContext (#314)
* Rework toolkit support (#312)
* Always instantiate Pinger on the thread it'll be used on (#309)
* Rename pinger modules (#308)
* Extract toolkit-specific EventLoopHelper from the GuiTestAssistant (#307)
* Add Pingee.pinger method (#306)
* Rename traits_futures.null to traits_futures.asyncio (#300)
* Add IPingee and IPinger interfaces (#298)
* Add MultiprocessingContext, and adapt existing classes to use it. (#284)
* Add multiprocessing implementation of the message router interfaces (#283)
* Add message routing interfaces (#282)
* Fix an inaccurate comment (#279)
* Update copyright headers for 2021 (#276)
* Add testing for wxPython (#269)
* Turn off macOS builds on Travis CI (#267)
* Use gh-pages instead of gh-pages-staging (#264)
* Fix documentation build (#262)
* Add explicit Pingee connect and disconnect methods (#255)
* Simplify the wx event code (#256)
* Tweak Sphinx configuration (#259)
* Use the EDM executable instead of the batch file on Windows (#247)
* Refactor MessageRouter and toolkit support (#231)
* Support PySide2 Qt backend in Travis CI and Appveyor (#233)
* Fix trivial typo in comment: reources -> resources. (#232)
* CLN: Clean up of the base_future module (#226)
* Update changelog to mention read-only state (#223)
* Fix message_router module docstring (#221)
* CLN : Update super usage (#213)
* Rename _dispatch_message to _task_sent (#227)







Release 0.3.0
-------------

Release date: XXXX-XX-XX

Features
~~~~~~~~

* Multiprocessing support: the :class:`~.TraitsExecutor` can now submit
  background tasks to a process pool instead of a thread pool. Note: since this
  support has not yet been tested in the wild, this support is provisional -
  the API and the capabilities may change in a future release. Feedback is
  welcome!

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
* The ``cancel`` method of a future no longer raises :exc:`RuntimeError` when a
  future is not cancellable. Instead, it communicates the information via its
  return value. If a future is already done, or has previously been cancelled,
  calling ``cancel`` on that future does not change the state of the future,
  and returns ``False``. Otherwise it changes the future's state to
  ``CANCELLING`` state, requests cancellation of the associated task, and
  returns ``True``.
* The ``ITaskSpecification.background_task`` method has been renamed to
  ``task``.
* The ``ITaskSpecification.future`` method now requires a cancellation callback
  to be passed.

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
