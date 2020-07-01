# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Base class providing common pieces of the Future machinery.
"""

import logging

from traits.api import (
    Bool,
    Callable,
    HasStrictTraits,
    HasTraits,
    Instance,
    on_trait_change,
    Property,
)

from traits_futures.future_states import (
    CANCELLABLE_STATES,
    CANCELLED,
    CANCELLING,
    COMPLETED,
    DONE_STATES,
    EXECUTING,
    FutureState,
)

logger = logging.getLogger(__name__)


# Messages sent by the wrapper, and interpreted by the BaseFuture

#: Message sent when the target callable has completed.
DONE = "done"


class BaseFuture(HasStrictTraits):
    """
    Convenience base class for the various flavours of Future.

    This isn't yet well-defined enough, documented enough or tested enough
    to be considered a formal abstract base class.
    """

    #: The state of the background task, to the best of the knowledge of
    #: this future.
    state = FutureState

    #: True if this task can be cancelled, else False.
    cancellable = Property(Bool())

    #: True if we've received the final message from the background task,
    #: else False. `True` indicates either that the background task
    #: succeeded, or that it raised, or that it was cancelled.
    done = Property(Bool())

    def cancel(self):
        """
        Method that can be called from the main thread to
        indicate that the task should be cancelled (provided
        it hasn't already started running).
        """
        # In the interests of catching coding errors early in client
        # code, we're strict about what states we allow cancellation
        # from. Some applications may want to weaken the error below
        # to a warning, or just do nothing on an invalid cancellation.
        if not self.cancellable:
            raise RuntimeError("Can only cancel a queued or executing task.")
        self._cancel()
        self.state = CANCELLING

    # Private traits ##########################################################

    #: Callable called with no arguments to request cancellation of the
    #: background task.
    _cancel = Callable()

    #: Object that receives messages from the background task.
    _receiver = Instance(HasTraits)

    # Private methods #########################################################

    @on_trait_change("_receiver:message")
    def _process_message(self, message):
        message_type, message_arg = message
        method_name = "_process_{}".format(message_type)
        getattr(self, method_name)(message_arg)

    def _process_done(self, none):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self.state = COMPLETED
        else:
            self.state = CANCELLED

    def _get_cancellable(self):
        return self.state in CANCELLABLE_STATES

    def _get_done(self):
        return self.state in DONE_STATES

    def _state_changed(self, old_state, new_state):
        old_cancellable = old_state in CANCELLABLE_STATES
        new_cancellable = new_state in CANCELLABLE_STATES
        if old_cancellable != new_cancellable:
            self.trait_property_changed(
                "cancellable", old_cancellable, new_cancellable
            )

        old_done = old_state in DONE_STATES
        new_done = new_state in DONE_STATES
        if old_done != new_done:
            self.trait_property_changed("done", old_done, new_done)


def job_wrapper(background_job, sender, cancel_event):
    """
    Wrapper for callables submitted to the underlying executor.

    Parameters
    ----------
    background_job : callable
        Callable representing the background job. This will be called
        with arguments ``send`` and ``cancelled`..
    sender : MessageSender
        Object used to send messages.
    cancel_event : event-like
        Event used to check for cancellation requests.
    """
    try:
        cancelled = cancel_event.is_set
        send = sender.send_message

        with sender:
            if not cancelled():
                background_job(send, cancelled)
            send(DONE)
    except BaseException:
        logger.exception("Unexpected exception in background job.")
        raise
