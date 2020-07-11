..
   (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
   All rights reserved.

traits\_futures\.api module
===========================

.. automodule:: traits_futures.api

This module re-exports the following constants, functions and classes:

Executor
--------

- :class:`~.TraitsExecutor`

Task submission functions
-------------------------

- :func:`~.submit_call`
- :func:`~.submit_iteration`
- :func:`~.submit_progress`

Types of futures
----------------

- :class:`~.IFuture`
- :class:`~.CallFuture`
- :class:`~.IterationFuture`
- :class:`~.ProgressFuture`

Future states
-------------

- :attr:`~.FutureState`
- :data:`~.CANCELLED`
- :data:`~.CANCELLING`
- :data:`~.COMPLETED`
- :data:`~.EXECUTING`
- :data:`~.FAILED`
- :data:`~.WAITING`

Executor states
---------------

- :attr:`~.ExecutorState`
- :data:`~.RUNNING`
- :data:`~.STOPPING`
- :data:`~.STOPPED`

Parallelism contexts
--------------------

- :class:`~.IParallelContext`
- :class:`~.MultithreadingContext`
