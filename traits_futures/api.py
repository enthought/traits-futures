# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Core API for the traits_futures package.
"""
from traits_futures.background_call import CallFuture
from traits_futures.background_iteration import IterationFuture
from traits_futures.background_progress import ProgressFuture
from traits_futures.future_states import (
    CANCELLED,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    FutureState,
)
from traits_futures.traits_executor import (
    ExecutorState,
    RUNNING,
    STOPPED,
    STOPPING,
    TraitsExecutor,
)

__all__ = [
    # Different types of Future
    "CallFuture",
    "IterationFuture",
    "ProgressFuture",
    # Future states
    "FutureState",
    "CANCELLED",
    "CANCELLING",
    "COMPLETED",
    "EXECUTING",
    # Executor
    "TraitsExecutor",
    # Executor states
    "ExecutorState",
    "RUNNING",
    "STOPPING",
    "STOPPED",
]
