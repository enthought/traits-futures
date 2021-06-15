..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!


Overview
========

Why Traits Futures?
-------------------

XXX: Succint tl;dr one-liner here.

The GUI frameworks that we typically work with at Enthought are single-threaded
by design: when an application is started the main thread enters the GUI
framework's event loop, waiting for external inputs and dispatching appropriate
callbacks back to Python code. Those callbacks will all execute on the main
thread, and are serialised: only one callback can be executing at any one time,
and it must execute to completion before any other callback can execute.

A TraitsUI-based GUI using one of these frameworks faces two main problems
related to background calculations.

* If a calculation is run directly in the GUI thread (that is, the main
  thread) then the GUI is blocked while that calculation is executing: it
  cannot respond to user input (mouse events, keyboard events), and may
  not refresh when a window is resized or temporarily covered. This generally
  provides a poor user experience, and may lead some users to conclude
  that the application is broken.

* The obvious solution to the first problem is to push the calculation
  to a background thread. But now we encounter a second problem: typically,
  we want to update the GUI when the background calculation completes. But
  in general it's unsafe to modify a GUI object from a thread other than
  the main thread.

Traits Futures provides a mechanism for executing one or more tasks in
background threads while being able to update the GUI safely in response to
both completion of the background task and/or progress messages sent from the
background task.

How does it work?
-----------------

- Diagram showing worker pool and GUI thread; GUI thread has event loop
    executing.
  Background task executed in worker pool
  Future "lives" in GUI thread
  Message queue between them.
  SVG image?

Relies on a running event loop to receive events from the background tasks.
Note that the background tasks themselves don't care - they'll keep on
running regardless.


Do's and Don'ts
---------------

* Do use the provided Traits Futures mechanisms for communication
  from the background task to the foreground future.
* Don't modify shared state directly from the background task.
* Don't modify traits (especially public traits) directly from the background
  task.
* Do make copies of mutable objects before passing them to the background
  task.
* Do pass ``self.max_count`` instead of passing ``self`` and looking up
  ``max_count`` in the background task.
* Don't do blocking waits in your main thread. React, don't block.
* Do always make sure that you shut down your ``TraitsExecutor`` safety
  at the end of your test, or at application shutdown time.


Non-CPU-bound tasks
-------------------

The ideal Traits Futures background task is a pure function, computing (small,
immutable, pickleable) outputs from (small, immutable, pickleable) inputs,
and not depending on any mutable shared state. Typically it's CPU bound.

But: Traits Futures can be used for short-lived non-CPU-bound tasks. In some
ways it's even better for that use-case, since multiple CPU-bound threads is
generally problematic for Python. But: typically in this case you'll be
interacting with a service. Be careful about thread safety. Limit the
amount of code that needs to thread safe.

It's fine to use Traits Futures for long-running tasks, but be aware that
such a task will be blocking an entire worker, and mostly sitting idle.
It's not ideal.




* Do use Traits Futures if ...


* Don't use Traits Futures if ...
    - You don't have a GUI. Just use a thread pool and concurrent.futures,
      or execute in the main thread, or ...
    - You're running headless. But note that if you happen to already have
      Traits Futures code that needs to run headless, then that's possible.
