"""
Future states, used by both the background calls and background iterations.
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

#: Final states. If the future is in one of these states,
#: no more messages will be received from the background job.
FINAL_STATES = CANCELLED, FAILED, COMPLETED

#: States in which we're permitted to cancel.
CANCELLABLE_STATES = EXECUTING, WAITING

#: Trait type representing a future state.
FutureState = Enum(
    WAITING, EXECUTING, CANCELLING, COMPLETED, FAILED, CANCELLED)
