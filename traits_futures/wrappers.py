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
Wrappers for the background task callable and the foreground future.

These are used by the TraitsExecutor machinery.
"""

import logging

from traits.api import (
    HasStrictTraits,
    HasTraits,
    Instance,
    on_trait_change,
)

from traits_futures.exception_handling import marshal_exception
from traits_futures.i_future import IFuture

logger = logging.getLogger(__name__)


#: Prefix used for custom messages.
CUSTOM = "custom"

#: Prefix used for control messages.
CONTROL = "control"

# Control messages sent by the wrapper, and interpreted by the FutureWrapper.

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

    #: Future being wrapped
    future = Instance(IFuture)

    #: Object that receives messages from the background task.
    receiver = Instance(HasTraits)

    @on_trait_change("receiver:message")
    def _receive_message(self, message):
        """
        Pass on a message to the appropriate future.
        """
        message_kind, message = message

        if message_kind == CUSTOM:
            self.future._dispatch_message(message)
        else:
            assert message_kind == CONTROL
            message_type, message_arg = message
            method_name = "_task_{}".format(message_type)
            getattr(self.future, method_name)(message_arg)


class BackgroundTaskWrapper:
    """
    Wrapper for callables submitted to the underlying executor.

    Parameters
    ----------
    background_task : collections.abc.Callable
        Callable representing the background task. This will be called
        with arguments ``send`` and ``cancelled``.
    sender : MessageSender
        Object used to send messages.
    cancelled : collections.abc.Callable
        Zero-argument callable returning bool. This can be called to check
        whether cancellation has been requested.
    """

    def __init__(self, background_task, sender, cancel_event):
        self._background_task = background_task
        self._sender = sender
        self._cancel_event = cancel_event

    def __call__(self):
        try:
            with self._sender:
                self.send_control_message(STARTED)
                try:
                    result = (
                        None
                        if self._cancel_event.is_set()
                        else self._background_task(
                            self.send_custom_message, self._cancel_event.is_set
                        )
                    )
                except BaseException as e:
                    self.send_control_message(RAISED, marshal_exception(e))
                else:
                    self.send_control_message(RETURNED, result)
        except BaseException:
            # We'll only ever get here in the case of a coding error. But in
            # case that happens, it's useful to have the exception logged to
            # help the developer.
            logger.exception("Unexpected exception in background task.")
            raise

    def send_control_message(self, message_type, message_args=None):
        """
        Send a control message from the background task to the future.

        These messages apply to all futures, and are used to communicate
        changes to the state of the future.
        """
        self._sender.send((CONTROL, (message_type, message_args)))

    def send_custom_message(self, message_type, message_args=None):
        """
        Send a custom message from the background task to the future.

        Parameters
        ----------
        message_type : str
            The message type.
        message_args : object, optional
            Any arguments providing additional information for the message.
            If not given, ``None`` is passed.
        """
        self._sender.send((CUSTOM, (message_type, message_args)))
