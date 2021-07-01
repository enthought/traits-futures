..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!

Traits Futures: reactive background processing for Traits and TraitsUI
======================================================================

Release v\ |release|.

The |traits_futures| package provides a means to fire off a background
calculation from a `TraitsUI`_ application, and later respond to the result(s)
of that calculation, leaving the main UI responsive for user interactions while
the background calculation is in progress.


Features
--------

- Supports simple calls, iterations, and progress-reporting functions. Can
  easily be extended to support other messaging patterns.
- Dispatching a background task returns a "future" object, which provides:

  - information about state changes (e.g., background task completion)
  - facilities to (cooperatively) cancel a long-running background task
  - access to result(s) arriving from the background task

- Future objects are |HasTraits| instances, suitable for integration
  into a TraitsUI application.
- No need to be a threading expert! Incoming results arrive as trait changes in
  the main thread. This eliminates a large class of potential issues with
  traditional thread-based solutions (race conditions, deadlocks, and UI
  updates off the main thread).
- Cross-platform.


Limitations
-----------

- By design, and unlike :mod:`concurrent.futures`, |traits_futures| requires the
  UI event loop to be running in order to process results.
- Requires Python 3.6 or later.


Quick start
-----------

Here's a :download:`complete example <examples/quick_start.py>` showing a
minimal TraitsUI application that fires off a background computation when its
"Calculate" button is pressed, and shows the result when it arrives.

.. literalinclude:: examples/quick_start.py
   :start-after: Thanks for using Enthought
   :lines: 2-


User Guide
==========

.. toctree::
   :maxdepth: 4

   guide/overview.rst
   guide/intro.rst
   guide/cancel.rst
   guide/contexts.rst
   guide/toolkits.rst
   guide/testing.rst
   guide/advanced.rst


API Documentation
=================

.. toctree::
   :maxdepth: 4

   api/traits_futures.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

..
   external links

.. _TraitsUI: https://docs.enthought.com/traitsui

..
   substitutions

.. |traits_futures| replace:: :mod:`traits_futures`
.. |HasTraits| replace:: :class:`~traits.has_traits.HasTraits`
