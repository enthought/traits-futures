"""
Background task consisting of a simple callable.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits.api import (
    Any, Bool, Callable, Dict, HasStrictTraits, Instance, Property, Str, Tuple)

from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLED, CANCELLING, EXECUTING, FAILED, COMPLETED, WAITING,
    FINAL_STATES, CANCELLABLE_STATES, FutureState)

# Message types for messages from CallBackgroundTask to CallFuture.
# The background task will emit exactly one of the following
# sequences of message types:
#
#   [INTERRUPTED]
#   [STARTED, RAISED]
#   [STARTED, RETURNED]

#: Call was cancelled before it started. No arguments.
INTERRUPTED = "interrupted"

#: Call started executing. No arguments.
STARTED = "started"

#: Call failed with an exception. Argument gives exception information.
RAISED = "raised"

#: Call succeeded and returned a result. Argument is the result.
RETURNED = "returned"


class CallBackgroundTask(object):
    """
    Wrapper around the actual callable to be run. This wrapper provides the
    task that will be submitted to the concurrent.futures executor
    """
    def __init__(self, callable, args, kwargs, message_sender, cancel_event):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.message_sender = message_sender
        self.cancel_event = cancel_event

    def __call__(self):
        with self.message_sender:
            if self.cancel_event.is_set():
                self.send(INTERRUPTED)
            else:
                self.send(STARTED)
                try:
                    result = self.callable(*self.args, **self.kwargs)
                except BaseException as e:
                    self.send(RAISED, marshal_exception(e))
                else:
                    self.send(RETURNED, result)

    def send(self, message_type, message_args=None):
        """
        Send a message to the foreground controller.
        """
        self.message_sender.send((message_type, message_args))


# CallFuture states. These represent the future's current
# state of knowledge of the background task. A task starts out
# in WAITING state and ends in one of the three final states:
# COMPLETED, FAILED, OR CANCELLED. The possible progressions of states are:
#
# WAITING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> FAILED
# WAITING -> EXECUTING -> COMPLETED


class CallFuture(HasStrictTraits):
    """
    Object representing the front-end handle to a background call.
    """
    #: The state of the background call, to the best of the knowledge of
    #: this future.
    state = FutureState

    #: True if we've received the final message from the background task,
    #: else False. `True` indicates either that the background task
    #: succeeded, or that it raised, or that it was cancelled.
    completed = Property(Bool, depends_on='state')

    #: True if this task can be cancelled, else False.
    cancellable = Property(Bool, depends_on='state')

    @property
    def result(self):
        """
        Result of the background call. Raises an ``Attributerror`` on access if
        no result is available (because the background call failed, was
        cancelled, or has not yet completed).

        Note: this is deliberately a regular Python property rather than a
        Trait, to discourage users from attaching Traits listeners to
        it. Listen to the state or its derived traits instead.
        """
        if self.state != COMPLETED:
            raise AttributeError("No result available for this call.")
        return self._result

    @property
    def exception(self):
        """
        Information about any exception raised by the background call. Raises
        an ``AttributeError`` on access if no exception was raised (because the
        call succeeded, was cancelled, or has not yet completed).

        Note: this is deliberately a regular Python property rather than a
        Trait, to discourage users from attaching Traits listeners to
        it. Listen to the state or its derived traits instead.
        """
        if self.state != FAILED:
            raise AttributeError("No exception has been raised for this call.")
        return self._exception

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
        self._cancel_event.set()
        self.state = CANCELLING

    def process_message(self, message):
        """
        Process a message from the background task.

        Parameters
        ----------
        message : tuple (string, any)
            Message from the background task. The first part is the
            message type, and the second part provides any message
            arguments.

        Returns
        -------
        bool
            True if this message represents the final communication
            from the background job, else False.
        """
        message_type, message_arg = message
        method_name = "_process_{}".format(message_type)
        getattr(self, method_name)(message_arg)
        return self.completed

    # Private traits ##########################################################

    #: Private event used to request cancellation of this task. Users
    #: should call the cancel() method instead of using this event.
    _cancel_event = Any

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Str, Str, Str)

    #: Object that receives messages from the background task.
    _message_receiver = Instance(HasStrictTraits)

    # Private methods #########################################################

    def _process_interrupted(self, arg):
        assert self.state in (CANCELLING,)
        self.state = CANCELLED

    def _process_started(self, arg):
        assert self.state in (WAITING, CANCELLING)
        if self.state == WAITING:
            self.state = EXECUTING

    def _process_raised(self, arg):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._exception = arg
            self.state = FAILED
        else:
            self.state = CANCELLED

    def _process_returned(self, arg):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._result = arg
            self.state = COMPLETED
        else:
            self.state = CANCELLED

    def _get_cancellable(self):
        return self.state in CANCELLABLE_STATES

    def _get_completed(self):
        return self.state in FINAL_STATES


class BackgroundCall(HasStrictTraits):
    """
    Object representing the background call to be executed.
    """
    #: The callable to be executed.
    callable = Callable

    #: Positional arguments to be passed to the callable.
    args = Tuple

    #: Named arguments to be passed to the callable.
    kwargs = Dict(Str, Any)

    def prepare(self, cancel_event, message_sender, message_receiver):
        """
        Prepare the task for running.

        Returns a pair (future, background_call), where
        the future acts as a handle for task cancellation, etc.,
        and the background_call is a callable to be executed
        in the background.
        """
        future = CallFuture(
            _cancel_event=cancel_event,
            _message_receiver=message_receiver,
        )
        runner = CallBackgroundTask(
            callable=self.callable,
            args=self.args,
            # Convert TraitsDict to a regular dict
            kwargs=dict(self.kwargs),
            message_sender=message_sender,
            cancel_event=cancel_event,
        )
        return future, runner


def background_call(callable, *args, **kwargs):
    """
    Convenience function for creating BackgroundCall objects.
    """
    return BackgroundCall(callable=callable, args=args, kwargs=kwargs)
