# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Wrappers for the background task callable and the foreground future.

These are used by the TraitsExecutor machinery.
"""

import logging

from traits.api import Bool, HasStrictTraits, HasTraits, Instance, observe

from traits_futures.i_future import IFuture

logger = logging.getLogger(__name__)


class FutureWrapper(HasStrictTraits):
    """
    Wrapper for the IFuture.

    Passes on messages received for this future.
    """

    #: The Traits Futures future being wrapped
    future = Instance(IFuture)

    #: Object that receives messages from the background task.
    receiver = Instance(HasTraits)

    #: Bool recording whether the future has completed or not. The
    #: executor listens to this trait to decide when it can clean up
    #: its own internal state.
    done = Bool(False)

    @observe("future:done")
    def _update_done_trait(self, event):
        """
        Update our own 'done' trait to reflect the future's 'done' trait.
        """
        self.done = event.new

    @observe("receiver:message")
    def _dispatch_to_future(self, event):
        """
        Pass on a message to the future.
        """
        self.future._message = event.new


def run_background_task(background_task, sender, cancelled):
    """
    Wrapper for callables submitted to the underlying executor.

    Parameters
    ----------
    background_task : collections.abc.Callable
        Callable representing the background task. This will be called
        with arguments ``send`` and ``cancelled``.
    sender : IMessageSender
        Object used to send messages.
    cancelled : collections.abc.Callable
        Zero-argument callable returning bool, used to check whether
        cancellation has been requested.
    """
    try:
        with sender:
            background_task(sender.send, cancelled)
    except BaseException:
        # We'll only ever get here in the case of a coding error. But in
        # case that happens, it's useful to have the exception logged to
        # help the developer.
        logger.exception("Unexpected exception in background task.")
        raise
