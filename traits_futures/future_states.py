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

#: Task cancelled.
CANCELLED = "cancelled"

#: Execution completed normally.
COMPLETED = "completed"

#: Trait type representing a future state.
FutureState = Enum(
    WAITING,  # default value
    [WAITING, EXECUTING, COMPLETED, CANCELLING, CANCELLED],
)
