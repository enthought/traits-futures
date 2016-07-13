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
# XXX The Job itself should be responsible for maintaining invariants, etc.
#     Transitions should be methods. The controller should merely hand off
#     responsibility to the appropriate job; it just becomes a message router.
#     E.g.: there should be a method to construct and return a JobRunner from
#     the job; that same method should set the state to QUEUED. Then there
#     should be methods to handle the messages from the job runner.

import threading

from traits.api import (
    Any, Callable, Dict, Enum, Event, HasStrictTraits, Str, Tuple)

from traits_futures.job_runner import (
    JobRunner,
    INTERRUPTED,
    RAISED,
    RETURNED,
    STARTING,
)


#: Job not yet submitted.
IDLE = "Idle"

#: Job is queued, and waiting to execute.
QUEUED = "Queued"

#: Job is executing.
EXECUTING = "Executing"

#: Job has completed, either returning a result, raising an
#: exception, or returning after cancellation.
COMPLETED = "Completed"

#: Job has been cancelled; awaiting completion.
CANCELLING = "Cancelling"


class Job(HasStrictTraits):
    #: The callable to be executed.
    job = Callable

    #: Arguments to be passed to the job.
    args = Tuple

    #: Keyword arguments.
    kwargs = Dict(Str, Any)

    #: The state of this job.
    state = Enum(IDLE, QUEUED, EXECUTING, COMPLETED, CANCELLING)

    #: Event fired when the callable completes normally. The payload
    #: of the event is the result of the job.
    result = Event

    #: Event fired when the callable fails due to an exception.
    #: The payload contains exception information.
    exception = Event

    #: Event used to request cancellation of this job.
    _cancel_event = Any

    def prepare(self, results_queue, job_id):
        """
        Prepare the job for running, and return a callable
        with no arguments that represents the background run.
        """
        if self.state != IDLE:
            raise RuntimeError("Cannot prepare job twice.")

        runner = JobRunner(
            job=self,
            job_id=job_id,
            results_queue=results_queue,
        )
        self.state = QUEUED
        return runner

    def cancel(self):
        """
        Method that can be called from the main thread to
        indicate that the job should be cancelled (provided
        it hasn't already started running).
        """
        state = self.state
        if state == IDLE:
            raise RuntimeError("Job has not been scheduled; cannot cancel.")
        elif state == COMPLETED:
            raise RuntimeError("Can't cancel a completed job.")
        elif state in (QUEUED, EXECUTING):
            self.state = CANCELLING
        elif state == CANCELLING:
            # Cancel should be idempotent.
            pass
        else:
            raise ValueError("Unexpected state: {}".format(state))
        self._cancel_event.set()

    def process_message(self, message):
        msg_type, msg_args = message
        if msg_type == STARTING:
            self._process_starting(msg_args)
        elif msg_type == RETURNED:
            self._process_returned(msg_args)
        elif msg_type == RAISED:
            self._process_raised(msg_args)
        elif msg_type == INTERRUPTED:
            self._process_interrupted(msg_args)
        else:
            raise ValueError(
                "Unrecognised message type: {!r}".format(msg_type))
        # Have we finished?
        return self.state == COMPLETED

    def _process_interrupted(self, args):
        assert self.state == CANCELLING
        self.state = COMPLETED

    def _process_raised(self, args):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self.exception = args
        self.state = COMPLETED

    def _process_returned(self, args):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self.result = args
        self.state = COMPLETED

    def _process_starting(self, args):
        assert self.state in (QUEUED, CANCELLING)
        if self.state == QUEUED:
            self.state = EXECUTING

    def __cancel_event_default(self):
        return threading.Event()
