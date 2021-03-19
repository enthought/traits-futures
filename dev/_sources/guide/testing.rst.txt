..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!


Testing Traits Futures code
===========================

This section gives some hints and tips for unit-testing code that uses
Traits Futures. Those tests face two main challenges:

- By design, Traits Futures relies on a running GUI event loop; that typically
  means that each test that uses Traits Futures will need to find some way to
  run the event loop in order for futures to deliver their results.
- It's important to fully shut down executors after each test, to avoid
  leaked threads and potential for test interactions.


An example test
---------------

Here's an example of testing a simple future.

.. literalinclude:: examples/test_future.py

Some points of interest in the above example:

- In order for the result of our future execution to be delivered to the main
  thread (a.k.a. the GUI thread), the event loop for the main thread needs to
  be running. We make use of the |GuiTestAssistant| class from Pyface
  to make it easy to run the event loop until a particular condition occurs.
- In the main test method, after submitting the call and receiving the
  ``future`` future, we want to wait until the future has completed and all
  communications from the background task have completed. We do that by using
  the |assertEventuallyTrueInGui| method. At that point, we can check that the
  result of the future is the expected one.
- We also need to shut down the executor itself at the end of the test. Note
  that the |stop| method is not blocking and does not actually stop the
  executor - instead, it requests cancellation of all running futures and
  prevents new jobs from being scheduled. For the executor to eventually reach
  the |STOPPED| state, the GUI event loop must again be running, so we make a
  second use of |assertEventuallyTrueInGui| in the ``tearDown`` method in the
  example.

If you don't need the result of the future (for example because you're using
the future for its side-effect rather than to perform a computation) then it's
safe to remove the wait for ``future.done``, so long as you keep the |stop|
call and then wait for the executor to stop: the executor won't reach |STOPPED|
state until all futures have completed.


.. |assertEventuallyTrueInGui| replace:: :meth:`pyface.ui.qt4.util.gui_test_assistant.GuiTestAssistant.assertEventuallyTrueInGui`
.. |GuiTestAssistant| replace:: :class:`pyface.ui.qt4.util.gui_test_assistant.GuiTestAssistant`

.. |stop| replace:: :meth:`~traits_futures.traits_executor.TraitsExecutor.stop`
.. |STOPPED| replace:: :meth:`~traits_futures.traits_executor.STOPPED`
