"""
Background task consisting of a simple callable.
"""
from traits.api import (
    Any, Bool, Callable, Dict, Either, Enum, HasStrictTraits, Int, Property,
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
INTERRUPTED = "Interrupted"

#: Call started executing.
STARTED = "Started"

#: Call failed with an exception.
RAISED = "Raised"

#: Call succeeded and returned a result.
RETURNED = "Returned"


class CallBackgroundTask(object):
    """
    Wrapper around the actual callable to be run. This wrapper
    provides the task that the concurrent.futures executor
    will use.
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
        self.results_queue.put((self.job_id, (message_type, message_args)))


# CallFuture states. These represent the future's current
# state of knowledge of the background task. A task starts out
# in WAITING state and ends in one of the three final states:
# SUCCEEDED, FAILED, OR CANCELLED.

#: Task queued, waiting to be executed.
WAITING = "Waiting"

#: Task is executing.
EXECUTING = "Executing"

#: Task has been cancelled; awaiting completion.
CANCELLING = "Cancelling"

#: Task succeeded, returning a result.
SUCCEEDED = "Succeeded"

#: Task failed, raising an exception.
FAILED = "Failed"

#: Task completed following cancellation.
CANCELLED = "Cancelled"

#: Trait type representing the state of a CallFuture.
CallFutureState = Enum(
    WAITING, EXECUTING, CANCELLING, SUCCEEDED, FAILED, CANCELLED)


class CallFuture(HasStrictTraits):
    """
    Object representing the front-end handle to a background job.
    """
    #: The state of this job.
    state = CallFutureState

    #: Trait set when the callable completes normally.
    result = Any

    #: Trait set when the callable fails due to an exception.
    #: The value gives a marshalled form of the exception: three
    #: strings representing the exception type, the exception value
    #: and the exception traceback.
    exception = Either(None, Tuple(Str, Str, Str))

    #: True if we've received the final message from the background job,
    #: else False.
    completed = Property(Bool, depends_on='state')

    #: True if this job can be cancelled (and hasn't already been cancelled),
    #: else False.
    cancellable = Property(Bool, depends_on='state')

    #: Private event used to request cancellation of this job. Users
    #: should call the cancel() method instead of using this event.
    _cancel_event = Any

    #: The id of this job. Potentially useful for debugging and logging.
    _job_id = Int()

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
        method_name = "_process_{}".format(msg_type.lower())
        getattr(self, method_name)(msg_args)
        return self.completed

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
            self.exception = args
            self.state = FAILED
        else:
            self.state = CANCELLED

    def _process_returned(self, args):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self.result = args
            self.state = SUCCEEDED
        else:
            self.state = CANCELLED

    def _get_cancellable(self):
        return self.state in (WAITING, EXECUTING)

    def _get_completed(self):
        return self.state in (SUCCEEDED, FAILED, CANCELLED)


class BackgroundCall(HasStrictTraits):
    #: The callable to be executed.
    callable = Callable

    #: Arguments to be passed to the callable.
    args = Tuple

    #: Keyword arguments to be passed to the callable.
    kwargs = Dict(Str, Any)

    def prepare(self, job_id, cancel_event, results_queue):
        """
        Prepare the job for running.

        Returns a pair (job_handle, background_call), where
        the job_handle acts as a handle for job cancellation, etc.,
        and the background_call is a callable to be executed
        in the background.
        """
        handle = CallFuture(
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
        return handle, runner


def background_call(callable, *args, **kwargs):
    """
    Convenience function for creating background tasks.
    """
    return BackgroundCall(callable=callable, args=args, kwargs=kwargs)
