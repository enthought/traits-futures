# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Core API for the traits_futures package.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits_futures.background_call import CallFuture
from traits_futures.background_iteration import IterationFuture
from traits_futures.background_progress import ProgressFuture
from traits_futures.future_states import (
    FutureState,
    CANCELLED,
    CANCELLING,
    EXECUTING,
    FAILED,
    COMPLETED,
    WAITING,
)
from traits_futures.traits_executor import (
    TraitsExecutor,
    ExecutorState,
    RUNNING,
    STOPPING,
    STOPPED,
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
]
