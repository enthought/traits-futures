# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Future states, used by the various future classes.
"""
from traits.api import Enum

#: Task is waiting to be executed.
WAITING = "waiting"

#: Task is executing.
EXECUTING = "executing"

#: Cancellation has been requested, awaiting response.
CANCELLING = "cancelling"

#: Task completed without error.
COMPLETED = "completed"

#: Task failed, raising an exception.
FAILED = "failed"

#: Task cancelled.
CANCELLED = "cancelled"

#: Trait type representing a future state.
FutureState = Enum(
    WAITING, EXECUTING, CANCELLING, COMPLETED, FAILED, CANCELLED
)
