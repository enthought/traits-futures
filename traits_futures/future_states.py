# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Future states, used by the various future classes.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits.api import Enum

#: Task queued, waiting to be executed.
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

#: States in which we're permitted to cancel.
CANCELLABLE_STATES = EXECUTING, WAITING

#: Final states. If the future is in one of these states,
#: no more messages will be received from the background job.
DONE_STATES = CANCELLED, COMPLETED, FAILED

#: Trait type representing a future state.
FutureState = Enum(
    WAITING, EXECUTING, CANCELLING, COMPLETED, FAILED, CANCELLED)
