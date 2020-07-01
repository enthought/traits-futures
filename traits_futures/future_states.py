# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Future states, used by the various future classes.
"""
from traits.api import Enum

#: Task is executing or waiting to be executed.
EXECUTING = "waiting"

#: Cancellation has been requested, awaiting response.
CANCELLING = "cancelling"

#: Task cancelled.
CANCELLED = "cancelled"

#: Execution completed normally.
COMPLETED = "done"

#: States in which we're permitted to cancel.
CANCELLABLE_STATES = (EXECUTING,)

#: Final states. If the future is in one of these states,
#: no more messages will be received from the background job.
DONE_STATES = CANCELLED, COMPLETED

#: Trait type representing a future state.
FutureState = Enum(EXECUTING, COMPLETED, CANCELLING, CANCELLED)
