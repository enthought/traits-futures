..
   (C) Copyright 2018-2023 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!

Traits Futures allows a TraitsUI-based GUI application to execute one or more
background tasks without blocking the main GUI, and provides a mechanism
for that application to *safely* update the GUI in response to full or
partial results from the background tasks.

Detailed description
--------------------

GUI applications that want to perform a long-running task in response to user
interactions (for example, running a time-consuming calculation, or submitting
a complex search query to a remote database) face two major issues:

* If the task is executed directly on the main thread, it blocks the GUI event
  loop, making the entire application appear unresponsive to the user.
* It's not generally safe to update a GUI directly from a worker thread, so
  a task run on a worker thread needs to find a way to safely communicate
  events back to the main GUI thread.

For TraitsUI-based applications, Traits Futures provides a solution to these
issues, similar in principle to the Python standard library
``concurrent.futures`` package. Tasks are submitted to an executor, and on task
submission the executor immediately returns a "future" object. That "future"
object has observable attributes ("traits") representing the application's view
of the state of the background task. Rather than waiting on the future's state,
an interested observer can listen to updates to those traits and update the GUI
state as necessary when changes occur. The Traits Futures machinery ensures
that updates to the future's traits always occur on the main thread, freeing
observers from thread-safety concerns.

For further information, see the documentation pages at
https://docs.enthought.com/traits-futures/.
