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

from traits_futures.exception_handling import marshal_exception
from traits_futures.i_future import IFuture

logger = logging.getLogger(__name__)


# Messages sent by the BackgroundTaskWrapper, and interpreted by the
# FutureWrapper.

#: Custom message from the future. The argument is a pair
#: (message_type, message_args); the message type and message args
#: are interpreted by the future.
SENT = "sent"

#: Control message sent before we start to process the target callable.
#: The argument is always ``None``.
STARTED = "started"

#: Control message sent when an exception was raised by the background
#: callable. The argument is a tuple containing exception information.
RAISED = "raised"

#: Control message sent to indicate that the background callable succeeded
#: and returned a result. The argument is that result.
RETURNED = "returned"


class FutureWrapper(HasStrictTraits):
    """
    Wrapper for the IFuture.

    This wrapper handles control messages from the background task, and
    delegates custom messages to the future.
    """

    #: The Traits Futures future being wrapped
    future = Instance(IFuture)

    #: Object that receives messages from the background task.
    receiver = Instance(HasTraits)

    #: Bool recording whether the future has completed or not. The
    #: executor listens to this trait to decide when it can clean up
    #: its own internal state.
    done = Bool(False)

    @observe("receiver:message")
    def _dispatch_to_future(self, event):
        """
        Pass on a message to the future.
        """
        message = event.new
        message_type, message_arg = message
        method_name = "_task_{}".format(message_type)
        getattr(self.future, method_name)(message_arg)
        if message_type in {RAISED, RETURNED}:
            self.done = True


class BackgroundTaskWrapper:
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
        Zero-argument callable returning bool. This can be called to check
        whether cancellation has been requested.
    """

    def __init__(self, background_task, sender, cancelled):
        self._background_task = background_task
        self._sender = sender
        self._cancelled = cancelled

    def __call__(self):
        try:
            with self._sender:
                self._sender.send((STARTED, None))
                try:
                    if self._cancelled():
                        result = None
                    else:
                        result = self._background_task(
                            self._send_custom_message, self._cancelled
                        )
                except BaseException as e:
                    self._sender.send((RAISED, marshal_exception(e)))
                else:
                    self._sender.send((RETURNED, result))
        except BaseException:
            # We'll only ever get here in the case of a coding error. But in
            # case that happens, it's useful to have the exception logged to
            # help the developer.
            logger.exception("Unexpected exception in background task.")
            raise

    def _send_custom_message(self, message):
        """
        Send a custom message from the background task to the future.

        Parameters
        ----------
        message : object
            The message to be sent.
        """
        self._sender.send((SENT, message))
