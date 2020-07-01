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

#: Trait type representing a future state.
FutureState = Enum(EXECUTING, COMPLETED, CANCELLING, CANCELLED)
