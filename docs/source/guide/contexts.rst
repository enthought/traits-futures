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

By default, the |TraitsExecutor| submits its tasks to a thread pool: either
one supplied by the |TraitsExecutor| creator, or a dedicated thread pool
created by the executor itself.

In some cases, for example in the case of multiple heavily CPU-bound background
tasks, it may be desirable to run the background tasks in separate processes
instead. For this to work, the Traits Futures code needs to know that it
has to work internally with multiprocessing variants of the usual concurrency
primitives: events, queues, worker pools and the like.

This can be achieved through use of a *context*, or more specifically,
an object implementing the |IParallelContext| interface. A context provides
the executor with a way of creating related and compatible
concurrency constructs.

Traits Futures provides two different contexts: the |MultithreadingContext|
and the |MultiprocessingContext|. By default, the executor will use a
|MultithreadingContext|, but you can create and pass in your own context
instead.
