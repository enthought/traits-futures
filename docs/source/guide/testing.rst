..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!


.. _guide_testing:

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

Here's an :download:`example <examples/test_future.py>` of testing a simple
future.

.. literalinclude:: examples/test_future.py
   :start-after: Thanks for using Enthought
   :lines: 2-

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
- We also need to shut down the executor itself at the end of the test; we
  use the |shutdown| method for this.
- In all potentially blocking calls, we provide a timeout. This should help
  prevent a failing test from blocking the entire test run if something goes
  wrong. However, note that if the timeout on the |shutdown| method fails then
  in addition to the test failing you may see segmentation faults or other
  peculiar side-effects, especially at process termination time, as a result of
  pieces of cleanup occurring out of order.

If you don't need the result of the future (for example because you're using
the future for its side-effect rather than to perform a computation) then it's
safe to remove the wait for ``future.done``, so long as you keep the |shutdown|
call.


.. |assertEventuallyTrueInGui| replace:: ``assertEventuallyTrueInGui``
.. |GuiTestAssistant| replace:: ``GuiTestAssistant``

.. |shutdown| replace:: :meth:`~traits_futures.traits_executor.TraitsExecutor.shutdown`
