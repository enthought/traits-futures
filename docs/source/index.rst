..
   (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
   All rights reserved.

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

- Future objects are ``HasTraits`` instances, suitable for integration
  into a TraitsUI application.
- No need to be a threading expert! Incoming results arrive as trait changes in
  the main thread. This eliminates a large class of potential issues with
  traditional thread-based solutions (race conditions, deadlocks, and UI
  updates off the main thread).
- Cross-platform, and compatible with both Python 2 and Python 3.


Limitations
-----------

- By design, and unlike `concurrent_futures`_, |traits_futures| requires the
  UI event loop to be running in order to process results.
- For the moment, |traits_futures| requires Qt. Support for wxPython
  may arrive in a future release.
- No multiprocessing support yet. Maybe one day.


Quick start
-----------

Here's a complete example showing a minimal TraitsUI application that fires off
a background computation when its "Calculate" button is pressed, and shows the
result when it arrives.

.. literalinclude:: examples/quick_start.py


Detailed Documentation
======================

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   guide/intro.rst
   api/modules.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _TraitsUI: https://github.com/enthought/traitsui
.. _concurrent_futures: https://docs.python.org/3/library/concurrent.futures.html

..
   substitutions

.. |traits_futures| replace:: :mod:`traits_futures`
