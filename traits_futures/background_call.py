"""
Background task consisting of a simple callable.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits.api import (
    Any, Bool, Callable, Dict, Enum, HasStrictTraits, Int, Property,
    Str, Tuple)

from traits_futures.exception_handling import marshal_exception

# Message types for messages from CallBackgroundTask to CallFuture.
# The background task will emit exactly one of the following
# sequences of message types:
#
#   [INTERRUPTED]
#   [STARTED, RAISED]
#   [STARTED, RETURNED]

#: Call was cancelled before it started.
INTERRUPTED = "interrupted"

#: Call started executing.
STARTED = "started"

#: Call failed with an exception.
RAISED = "raised"

#: Call succeeded and returned a result.
RETURNED = "returned"


class CallBackgroundTask(object):
    """
    Wrapper around the actual callable to be run. This wrapper provides the
    task that will be submitted to the concurrent.futures executor
    """
    def __init__(
            self, job_id, callable, args, kwargs,
            results_queue, cancel_event):
        self.job_id = job_id
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.results_queue = results_queue
        self.cancel_event = cancel_event

    def __call__(self):
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

        Parameters
        ----------
        message_type : string
            One of
        """
        message = message_type, message_args
        self.results_queue.put((self.job_id, message))


# CallFuture states. These represent the future's current
# state of knowledge of the background task. A task starts out
# in WAITING state and ends in one of the three final states:
# SUCCEEDED, FAILED, OR CANCELLED. The possible progressions of states are:
#
# WAITING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> FAILED
# WAITING -> EXECUTING -> SUCCEEDED

#: Task queued, waiting to be executed.
WAITING = "waiting"

#: Task is executing.
EXECUTING = "executing"

#: Task has been cancelled; awaiting completion.
CANCELLING = "cancelling"

#: Task succeeded, returning a result.
SUCCEEDED = "succeeded"

#: Task failed, raising an exception.
FAILED = "failed"

#: Task completed following cancellation.
CANCELLED = "cancelled"

#: Trait type representing the state of a CallFuture.
CallFutureState = Enum(
    WAITING, EXECUTING, CANCELLING, SUCCEEDED, FAILED, CANCELLED)


class CallFuture(HasStrictTraits):
    """
    Object representing the front-end handle to a background call.
    """
    #: The state of the background call.
    state = CallFutureState

    #: True if we've received the final message from the background job,
    #: else False. `True` indicates either that the background job
    #: succeeded, or that it raised, or that it was cancelled.
    completed = Property(Bool, depends_on='state')

    #: True if this job can be cancelled, else False.
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
        if self.state == SUCCEEDED:
            return self._result
        else:
            raise AttributeError("No result available for this task.")

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
        if self.state == FAILED:
            return self._exception
        else:
            raise AttributeError("No exception has been raised for this task.")

    def cancel(self):
        """
        Method that can be called from the main thread to
        indicate that the job should be cancelled (provided
        it hasn't already started running).
        """
        if not self.cancellable:
            # Might want to downgrade this to a warning. But a good UI
            # will ensure that the Cancel button can only be pushed if
            # we're in a cancellable state.
            raise RuntimeError("Can only cancel a queued or executing job.")
        self._cancel_event.set()
        self.state = CANCELLING

    def process_message(self, message):
        """
        Process a message from the background job.
        """
        msg_type, msg_args = message
        method_name = "_process_{}".format(msg_type)
        getattr(self, method_name)(msg_args)
        return self.completed

    # Private traits ##########################################################

    #: Private event used to request cancellation of this job. Users
    #: should call the cancel() method instead of using this event.
    _cancel_event = Any

    #: The id of this job. Potentially useful for debugging and logging.
    _job_id = Int()

    #: Result from the background task.
    _result = Any

    #: Exception information from the background task.
    _exception = Tuple

    # Private methods #########################################################

    def _process_interrupted(self, args):
        assert self.state in (CANCELLING,)
        self.state = CANCELLED

    def _process_started(self, args):
        assert self.state in (WAITING, CANCELLING)
        if self.state == WAITING:
            self.state = EXECUTING

    def _process_raised(self, args):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._exception = args
            self.state = FAILED
        else:
            self.state = CANCELLED

    def _process_returned(self, args):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._result = args
            self.state = SUCCEEDED
        else:
            self.state = CANCELLED

    def _get_cancellable(self):
        return self.state in (WAITING, EXECUTING)

    def _get_completed(self):
        return self.state in (SUCCEEDED, FAILED, CANCELLED)


class BackgroundCall(HasStrictTraits):
    """
    Object representing the background call to be executed.
    """
    #: The callable to be executed.
    callable = Callable

    #: Arguments to be passed to the callable.
    args = Tuple

    #: Keyword arguments to be passed to the callable.
    kwargs = Dict(Str, Any)

    def prepare(self, job_id, cancel_event, results_queue):
        """
        Prepare the job for running.

        Returns a pair (future, background_call), where
        the future acts as a handle for job cancellation, etc.,
        and the background_call is a callable to be executed
        in the background.
        """
        future = CallFuture(
            _job_id=job_id,
            _cancel_event=cancel_event,
        )
        runner = CallBackgroundTask(
            job_id=job_id,
            callable=self.callable,
            args=self.args,
            # Convert TraitsDict to a regular dict
            kwargs=dict(self.kwargs),
            results_queue=results_queue,
            cancel_event=cancel_event,
        )
        return future, runner


def background_call(callable, *args, **kwargs):
    """
    Convenience function for creating background tasks.
    """
    return BackgroundCall(callable=callable, args=args, kwargs=kwargs)
