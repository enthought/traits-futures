# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Future states, used by the various future classes.
"""
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
#: no more messages will be received from the background task.
DONE_STATES = CANCELLED, COMPLETED, FAILED

#: Trait type representing a future state.
FutureState = Enum(
    WAITING, EXECUTING, CANCELLING, COMPLETED, FAILED, CANCELLED
)
