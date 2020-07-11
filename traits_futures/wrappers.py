# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Wrappers for the background task callable and the foreground future.

These are used by the TraitsExecutor machinery.
"""

import logging

from traits.api import (
    Any,
    HasStrictTraits,
    HasTraits,
    Instance,
    on_trait_change,
)

from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLED,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    FAILED,
    WAITING,
)
from traits_futures.i_future import IFuture

logger = logging.getLogger(__name__)


# Messages sent by the wrapper, and interpreted by the BaseFuture

#: Message sent before we start to process the target callable.
STARTED = "started"

#: Message sent when an exception was raised by the background
#: callable. The argument is a tuple containing exception information.
RAISED = "raised"

#: Call succeeded and returned a result. Argument is the result.
RETURNED = "returned"

#: Prefix used for custom messages
CUSTOM = "custom"


class FutureWrapper(HasStrictTraits):
    #: Future being wrapped
    future = Instance(IFuture)

    #: Object that receives messages from the background task.
    receiver = Instance(HasTraits)

    #: Callable used to request cancellation
    cancel = Any()

    @on_trait_change("receiver:message")
    def _receive_message(self, message):
        """
        Pass on a message to the appropriate future.
        """
        if message[0] == CUSTOM:
            assert self.future.state in (CANCELLING, EXECUTING)
            self.future.message = message[1:]
            return

        message_type, message_args = message
        if message_type == STARTED:
            self._process_started(message_args)
        elif message_type == RAISED:
            self._process_raised(message_args)
        elif message_type == RETURNED:
            self._process_returned(message_args)
        else:
            raise RuntimeError("Unknown message type: {}".format(message_type))

    @on_trait_change("future:_cancel")
    def _do_cancellation(self):
        self.cancel()

    def _process_raised(self, exception_info):
        """
        Process a RAISED message from the background task.

        A task in EXECUTING state moves to FAILED state, and then the
        exception information is available through the future's ``exception``
        attribute.

        A task in CANCELLING state  moves to CANCELLED state, and the
        exception information is not made available to the future.
        """

        future = self.future
        assert future.state in (EXECUTING, CANCELLING)
        if future.state == EXECUTING:
            future._exception = exception_info
            future.state = FAILED
        else:
            future.state = CANCELLED

    def _process_returned(self, result):
        """
        Process a RETURNED message from the background task.

        A task in EXECUTING state moves to COMPLETED state, and then the
        exception information is available through the future's ``result``
        attribute.

        A task in CANCELLING state  moves to CANCELLED state, and the
        result information is not made available to the future.
        """
        future = self.future

        assert future.state in (EXECUTING, CANCELLING)
        if future.state == EXECUTING:
            future._result = result
            future.state = COMPLETED
        else:
            future.state = CANCELLED

    def _process_started(self, none):
        """
        Process a STARTED message from the background task.

        A task in WAITING STATE moves to EXECUTING state. A task in
        CANCELLING state remains in CANCELLING state.
        """
        future = self.future

        assert future.state in (WAITING, CANCELLING)
        if future.state == WAITING:
            future.state = EXECUTING


class BackgroundTaskWrapper:

    """
    Wrapper for callables submitted to the underlying executor.

    Parameters
    ----------
    background_task : callable
        Callable representing the background task. This will be called
        with arguments ``send`` and ``cancelled`..
    sender : MessageSender
        Object used to send messages.
    cancelled : zero-argument callable returning bool
        Callable that can be called to check whether cancellation has
        been requested.
    """

    def __init__(self, background_task, sender, cancelled):
        self._background_task = background_task
        self._sender = sender
        self._cancelled = cancelled

    def __call__(self):
        sender = self._sender
        cancelled = self._cancelled
        background_task = self._background_task

        try:
            send = sender.send_message
            send_custom = self.send_custom_message
            with sender:
                if cancelled():
                    send(RETURNED, None)
                else:
                    send(STARTED)
                    try:
                        result = background_task(send_custom, cancelled)
                    except BaseException as e:
                        send(RAISED, marshal_exception(e))
                    else:
                        send(RETURNED, result)
        except BaseException:
            # We'll only ever get here in the case of a coding error. But in
            # case that happens, it's useful to have the exception logged to
            # help the developer.
            logger.exception("Unexpected exception in background task.")
            raise

    def send_custom_message(self, message_type, message_args=None):
        self._sender.send((CUSTOM, message_type, message_args))
