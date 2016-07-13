# Notes: there should be a defined order for firing the result and firing the
# state change.  The state change should happen *after* firing the result or
# the exception events. Once the job is completed, that should guarantee that
# no further traits are fired, so a listener can wait for the state to become
# COMPLETED.

# XXX Should have a JobState trait type.
# XXX Add logging
# XXX Design: fold Job and JobRunner into a single class? Why not?
#     Job: needs to be friendly to use. Provides main-thread interface
#     to a running job.
#     JobRunner: needs to be pickleable, shouldn't need to hold
#       a reference to the Job object.

from traits.api import (
    Any, Bool, Callable, Dict, Enum, HasStrictTraits, Property, Str, Tuple)

from traits_futures.job_runner import JobRunner

# --- Job states --------------------------------------------------------------

#: Job not yet submitted.
IDLE = "Idle"

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


class Job(HasStrictTraits):
    #: The callable to be executed.
    callable = Callable

    #: Arguments to be passed to the callable.
    args = Tuple

    #: Keyword arguments to be passed to the callable.
    kwargs = Dict(Str, Any)

    #: The state of this job.
    state = Enum(IDLE, EXECUTING, CANCELLING, SUCCEEDED, FAILED, CANCELLED)

    #: Event fired when the callable completes normally. The payload
    #: of the event is the result of the job.
    result = Any

    #: Event fired when the callable fails due to an exception.
    #: The payload contains exception information.
    exception = Any

    #: True if we've received the final message from the background job,
    #: else False.
    completed = Property(Bool, depends_on='state')

    #: Event used to request cancellation of this job.
    _cancel_event = Any

    def prepare(self, job_id, cancel_event, results_queue):
        """
        Prepare the job for running, and return a callable
        with no arguments that represents the background run.
        """
        if self.state != IDLE:
            raise RuntimeError("Cannot prepare job twice.")
        self._cancel_event = cancel_event
        runner = JobRunner(job=self, job_id=job_id,
                           results_queue=results_queue)
        self.state = EXECUTING
        return runner

    def cancel(self):
        """
        Method that can be called from the main thread to
        indicate that the job should be cancelled (provided
        it hasn't already started running).
        """
        if self.state != EXECUTING:
            raise RuntimeError("Can only cancel an executing job.")
        self._cancel_event.set()
        self.state = CANCELLING

    def process_message(self, message):
        msg_type, msg_args = message
        method_name = "_process_{}".format(msg_type.lower())
        getattr(self, method_name)(msg_args)
        return self.completed

    # Private methods #########################################################

    def _process_interrupted(self, args):
        assert self.state == CANCELLING
        self.state = CANCELLED

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

    # Traits methods ##########################################################

    def _get_completed(self):
        return self.state in (SUCCEEDED, FAILED, CANCELLED)
