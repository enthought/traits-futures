..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!

Contexts and multiprocessing
============================

By default, the |TraitsExecutor| submits its background tasks to a thread pool.
In some cases, for example in the case of multiple heavily CPU-bound background
tasks, it may be desirable to run the background tasks in separate processes
instead. For this to work, the Traits Futures code needs to know that it has to
work internally with multiprocessing-safe variants of the usual concurrency
primitives: events, queues, worker pools and the like.

This can be achieved through use of a *context*, or more specifically,
an object implementing the |IParallelContext| interface. A context provides
the executor with a way of creating related and compatible
concurrency constructs.

Traits Futures provides two different contexts: the |MultithreadingContext|
and the |MultiprocessingContext|. By default, the executor will use a
|MultithreadingContext|, but you can create and pass in your own context
instead. The context should be closed with the |close| method once it's
no longer needed.

Here's an example ``main`` function that creates an executor that uses
a multiprocessing context::

    def main():
        context = MultiprocessingContext()
        traits_executor = TraitsExecutor(context=context)
        try:
            view = SquaringHelper(traits_executor=traits_executor)
            view.configure_traits()
        finally:
            traits_executor.stop()
            context.close()

Here's a complete TraitsUI example that makes use of this.

.. literalinclude:: examples/background_processes.py
   :start-after: Thanks for using Enthought
   :lines: 2-


..
   substitutions


.. |close| replace:: :meth:`~.IParallelContext.close`
.. |IParallelContext| replace:: :class:`~.IParallelContext`
.. |MultiprocessingContext| replace:: :class:`~.MultiprocessingContext`
.. |MultithreadingContext| replace:: :class:`~.MultithreadingContext`
.. |TraitsExecutor| replace:: :class:`~.TraitsExecutor`
