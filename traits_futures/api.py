# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Core API for the traits_futures package.
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
from traits_futures.i_job_specification import IJobSpecification
from traits_futures.i_parallel_context import IParallelContext
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
    # Convenience submission functions for job types that we define
    "submit_call",
    "submit_iteration",
    "submit_progress",
    # IJobSpecification: interface for creating new job types
    "IJobSpecification",
    # Contexts
    "IParallelContext",
    "MultithreadingContext",
]
