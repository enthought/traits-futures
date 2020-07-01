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
DONE = "done"

#: States in which we're permitted to cancel.
CANCELLABLE_STATES = (EXECUTING,)

#: Final states. If the future is in one of these states,
#: no more messages will be received from the background job.
FINAL_STATES = CANCELLED, DONE

#: Trait type representing a future state.
FutureState = Enum(EXECUTING, DONE, CANCELLING, CANCELLED)
