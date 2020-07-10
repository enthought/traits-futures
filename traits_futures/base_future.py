# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Base class providing common pieces of the Future machinery.
"""

import logging

from traits.api import (
    Any,
    Bool,
    Callable,
    HasTraits,
    Instance,
    on_trait_change,
    Property,
    Str,
    Tuple,
)

from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLED,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    FAILED,
    FutureState,
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

#: Message sent when the target callable has completed.
DONE = "done"

#: States in which the job can be cancelled.
CANCELLABLE_STATES = WAITING, EXECUTING

#: Final states. If the future is in one of these states,
#: no more messages will be received from the background job.
DONE_STATES = CANCELLED, COMPLETED, FAILED


class BaseFuture(IFuture):
    """
    Convenience base class for the various flavours of Future.
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

    @property
    def result(self):
        """
        Result of the background call. This is only available if:

        - the state of the future is COMPLETED
        - the call completed normally, without raising

        Returns
        -------
        result : object
            The result obtained from the background call.

        Raises
        ------
        AttributeError
            If the job is still executing, or was cancelled, or raised an
            exception instead of returning a result.
        """
        if self.state != COMPLETED:
            raise AttributeError(
                "No result available. Task has not yet completed, "
                "or was cancelled, or failed with an exception. "
                "Job status is {}".format(self.state)
            )
        return self._result

    @property
    def exception(self):
        """
        Information about any exception raised by the background call. Raises
        an ``AttributeError`` on access if no exception was raised (because the
        call succeeded, was cancelled, or has not yet completed).

        Returns
        -------
        exc_info : tuple(str, str, str)
            Tuple containing marshalled exception information.

        Raises
        ------
        AttributeError
            If the job is still executing, or was cancelled, or completed
            without raising an exception.
        """
        if self.state != FAILED:
            raise AttributeError(
                "No exception information available. Job has "
                "not yet completed, or was cancelled, or completed "
                "without an exception. "
                "Job status is {}".format(self.state)
            )
        return self._exception

    # Private traits ##########################################################

    #: Callable called with no arguments to request cancellation of the
    #: background task.
    _cancel = Callable()

    #: Object that receives messages from the background task.
    _receiver = Instance(HasTraits)

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    @on_trait_change("_receiver:message")
    def _process_message(self, message):
        message_type, message_arg = message
        method_name = "_process_{}".format(message_type)
        getattr(self, method_name)(message_arg)

    def _process_done(self, none):
        assert self.state in (CANCELLING,)
        self.state = CANCELLED

    def _process_raised(self, exception_info):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._exception = exception_info
            self.state = FAILED
        else:
            self.state = CANCELLED

    def _process_returned(self, result):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._result = result
            self.state = COMPLETED
        else:
            self.state = CANCELLED

    def _process_started(self, none):
        assert self.state in (WAITING, CANCELLING)
        if self.state == WAITING:
            self.state = EXECUTING

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

    def _raise_unless_completed(self):
        """
        Check that the job has completed, and raise AttributeError if not.
        """
        if self.state not in (COMPLETED, FAILED):
            raise AttributeError(
                "Job has not yet completed, or was cancelled. "
                "Job status is {}".format(self.state)
            )


def job_wrapper(background_job, sender, cancelled):
    """
    Wrapper for callables submitted to the underlying executor.

    Parameters
    ----------
    background_job : callable
        Callable representing the background job. This will be called
        with arguments ``send`` and ``cancelled`..
    sender : MessageSender
        Object used to send messages.
    cancelled : zero-argument callable returning bool
        Callable that can be called to check whether cancellation has
        been requested.
    """
    try:
        send = sender.send_message
        with sender:
            if cancelled():
                send(DONE)
            else:
                send(STARTED)
                try:
                    result = background_job(send, cancelled)
                except BaseException as e:
                    send(RAISED, marshal_exception(e))
                else:
                    send(RETURNED, result)
    except BaseException:
        # We'll only ever get here in the case of a coding error. But in
        # case that happens, it's useful to have the exception logged to
        # help the developer.
        logger.exception("Unexpected exception in background job.")
        raise