# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Core API for the traits_futures package.

This module represents the public API of the Traits Futures library. It
contains everything you should need as a user of the library. No stability
guarantees are made for imports from other modules or subpackages.

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

Support for user-defined background tasks
-----------------------------------------

- :class:`~.BaseFuture`
- :class:`~.ITaskSpecification`

Parallelism contexts
--------------------

- :class:`~.IParallelContext`
- :class:`~.MultithreadingContext`

"""
from traits_futures.background_call import (
    CallFuture,
    submit_call,
)
from traits_futures.background_iteration import (
    IterationFuture,
    submit_iteration,
)
from traits_futures.background_progress import (
    ProgressFuture,
    submit_progress,
)
from traits_futures.base_future import BaseFuture
from traits_futures.future_states import (
    CANCELLED,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    FAILED,
    FutureState,
    WAITING,
)
from traits_futures.i_future import IFuture
from traits_futures.i_parallel_context import IParallelContext
from traits_futures.i_task_specification import ITaskSpecification
from traits_futures.multithreading_context import MultithreadingContext
from traits_futures.traits_executor import (
    ExecutorState,
    RUNNING,
    STOPPED,
    STOPPING,
    TraitsExecutor,
)

__all__ = [
    # Different types of Future
    "IFuture",
    "CallFuture",
    "IterationFuture",
    "ProgressFuture",
    # Future states
    "FutureState",
    "CANCELLED",
    "CANCELLING",
    "EXECUTING",
    "FAILED",
    "COMPLETED",
    "WAITING",
    # Executor
    "TraitsExecutor",
    # Executor states
    "ExecutorState",
    "RUNNING",
    "STOPPING",
    "STOPPED",
    # Convenience submission functions for task types that we define
    "submit_call",
    "submit_iteration",
    "submit_progress",
    # Support for creating new task types
    "BaseFuture",
    "ITaskSpecification",
    # Contexts
    "IParallelContext",
    "MultithreadingContext",
]
