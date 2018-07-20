# XXX Should have a JobState trait type.
# XXX Add logging

from traits.api import (
    Any, Bool, Callable, Dict, Either, Enum, HasStrictTraits, Int, Property,
    Str, Tuple)

from traits_futures.exception_handling import marshal_exception

# Job runner messages.

#: Job was cancelled before it started.
INTERRUPTED = "Interrupted"

#: Job failed with an exception.
RAISED = "Raised"

#: Job succeeded and returned a result.
RETURNED = "Returned"

#: Job started executing.
STARTED = "Started"

# JobHandle states.

#: Job queued, waiting to be executed.
WAITING = "Waiting"

#: Job is executing.
EXECUTING = "Executing"

#: Job has been cancelled; awaiting completion.
CANCELLING = "Cancelling"

#: Job succeeded, returning a result.
SUCCEEDED = "Succeeded"

#: Job failed, raising an exception.
FAILED = "Failed"

#: Job completed following cancellation.
CANCELLED = "Cancelled"


class JobRunner(object):
    """
    Wrapper around the actual callable to be run. This wrapper
    provides the callable that the concurrent.futures executor
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


class JobHandle(HasStrictTraits):
    """
    Object representing the front-end handle to a background job.
    """
    #: The id of this job.
    job_id = Int()

    #: The state of this job.
    state = Enum(WAITING, EXECUTING, CANCELLING, SUCCEEDED, FAILED, CANCELLED)

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

    #: Event used to request cancellation of this job.
    cancel_event = Any

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
        self.cancel_event.set()
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


class Job(HasStrictTraits):
    #: The callable to be executed.
    callable = Callable

    #: Arguments to be passed to the callable.
    args = Tuple

    #: Keyword arguments to be passed to the callable.
    kwargs = Dict(Str, Any)

    def prepare(self, job_id, cancel_event, results_queue):
        """
        Prepare the job for running.

        Returns a pair (job_handle, background_job), where
        the job_handle acts as a handle for job cancellation, etc.,
        and the background_job is a callable to be executed
        in the background.
        """
        handle = JobHandle(
            job_id=job_id,
            cancel_event=cancel_event,
        )
        runner = JobRunner(
            job_id=job_id,
            callable=self.callable,
            args=self.args,
            # Convert TraitsDict to a regular dict
            kwargs=dict(self.kwargs),
            results_queue=results_queue,
            cancel_event=cancel_event,
        )
        return handle, runner


def background_job(callable, *args, **kwargs):
    """
    Convenience function for creating background tasks.
    """
    return Job(callable=callable, args=args, kwargs=kwargs)
