# Notes: there should be a defined order for firing the result and firing the
# state change.  The state change should happen *after* firing the result or
# the exception events. Once the job is completed, that should guarantee that
# no further traits are fired, so a listener can wait for the state to become
# COMPLETED / CANCELLED.

# XXX Should have a JobState trait type.
# XXX Add logging
# XXX Design: fold Job and JobRunner into a single class? Why not?

from traits.api import (
    Any, Callable, Dict, Enum, Event, HasStrictTraits, Str, Tuple)

#: Job not yet submitted.
IDLE = "Idle"

#: Job is queued, and waiting to execute.
QUEUED = "Queued"

#: Job is executing.
EXECUTING = "Executing"

#: Job has completed, either returning a result or raising an
#: exception.
COMPLETED = "Completed"

#: Job has been cancelled.
CANCELLED = "Cancelled"


class Job(HasStrictTraits):
    #: The callable to be executed.
    job = Callable

    #: Arguments to be passed to the job.
    args = Tuple

    #: Keyword arguments.
    kwargs = Dict(Str, Any)

    #: The state of this job.
    state = Enum(IDLE, QUEUED, EXECUTING, COMPLETED, CANCELLED)

    #: Event fired when the callable completes normally. The payload
    #: of the event is the result of the job.
    result = Event

    #: Event fired when the callable fails due to an exception.
    #: The payload contains exception information.
    exception = Event

    def __call__(self):
        return self.job(*self.args, **self.kwargs)
