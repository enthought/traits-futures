Traits Futures: reactive background processing for Traits and TraitsUI
======================================================================

Release v\ |release|.

The **traits-futures** package provides a means to fire off a background
calculation from a `TraitsUI`_ application, and later respond to the result(s)
of that calculation, leaving the main UI responsive for user interactions while
the background calculation is in progress.


Features
--------

- Supports simple calls, iterations, and progress-reporting functions. Can
  easily be extended with other messaging patterns.
- Dispatching a background task returns a "future" object.
- State changes (e.g., background task completion) are signalled as
  trait changes on the "future" object.
- The "future" object can be directly interrogated to determine the
  state of the background task.
- No need to be a threading expert! Incoming results arrive as Trait
  changes in the main thread. This eliminates a large class of
  potential issues with race conditions, deadlocks, and UI updates
  off the main thread.
- Support for (cooperative) background task cancellation.
- Cross-platform, and compatible with both Python 2 and Python 3.


Limitations
-----------

- By design, and unlike ``concurrent.futures``, ``traits-futures`` requires the
  UI event loop to be running in order to process results.
- For the moment, ``traits-futures`` requires Qt. Support for wxPython
  may arrive in a future release.
- No multiprocessing support yet. Maybe one day.


Quick start
-----------

Here's a complete example showing a minimal TraitsUI application that fires off
a background computation when its "Calculate" button is pressed, and shows the
result when it arrives.

.. literalinclude:: examples/quick_start.py


API Documentation
=================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/modules.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _TraitsUI: https://github.com/enthought/traitsui
