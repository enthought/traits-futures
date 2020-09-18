..
   (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!

Changelog for Traits Futures
============================


Release 0.2.0
-------------

Release date: XXXX-XX-XX

Features
~~~~~~~~

- ``TraitsExecutor`` now accepts a ``max_workers`` argument, which will
  be used to specify the number of workers if the executor creates its own
  worker pool.

Changes
~~~~~~~

- The ``thread_pool`` argument to ``TraitsExecutor`` has been renamed to
  ``worker_pool``. The old name ``thread_pool`` continues to work, but its
  use is deprecated.

- The ``submit_call``, ``submit_iteration`` and ``submit_progress`` methods
  on the ``TraitsExecutor`` have been deprecated. Use the new top-level
  convenience functions with the same names instead.

- The default number of workers in the worker pool has changed. Previously
  it was hard-coded as ``4``. Now it defaults to whatever Python's
  ``concurrent.futures`` executors give (but it can be controlled by
  passing the ``max_workers`` argument).


Release 0.1.1
-------------

Release date: 2019-02-05

This is a bugfix release, in preparation for the first public release to PyPI. There
are no functional or API changes to the core library since 0.1.0 in this release.

Fixes
~~~~~

- Add missing ``long_description`` field in setup script. (#116, backported in #118)

Changes
~~~~~~~

- Add copyright headers to all Python and reST files. (#114, backported in #118)

Build
~~~~~

- Remove unnecessary bundle generation machinery. (#99, backported in #118)


Release 0.1.0
-------------

Release date: 2018-08-08

Initial release. Provides support for submitting background calls, iterations,
and progress-reporting tasks for Traits UI applications based on Qt.
