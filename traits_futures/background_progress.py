# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Support for a progress-reporting background call.

The code in this module supports an arbitrary callable that accepts a
"progress" named argument, and can use that argument to submit progress
information.

Every progress submission also marks a point where the callable can
be cancelled.
"""

from traits.api import (
    Any,
    Bool,
    Callable,
    Dict,
    Event,
    HasStrictTraits,
    Str,
    Tuple,
)

from traits_futures.base_future import BaseFuture
from traits_futures.future_states import (
    CANCELLING,
    COMPLETED,
    EXECUTING,
)
from traits_futures.i_job_specification import IJobSpecification


# Message types for messages from ProgressBackgroundTask
# to ProgressFuture.

#: Task succeeded and returned a result. Argument is the result.
RETURNED = "returned"

#: Task sends progress. Argument is a single object giving progress
#: information. This module does not interpret the contents of the argument.
PROGRESS = "progress"


class _ProgressCancelled(Exception):
    """
    Exception raised when progress reporting is interrupted by
    task cancellation.
    """


class ProgressReporter:
    """
    Object used by the target callable to report progress.
    """

    def __init__(self, send, cancelled):
        self.send = send
        self.cancelled = cancelled

    def report(self, progress_info):
        """
        Send progress information to the linked future.

        The ``progress_info`` object will eventually be sent to the
        corresponding future's ``progress`` event trait.

        Parameters
        ----------
        progress_info : object
            An arbitrary object representing progress. Ideally, this
            should be immutable and pickleable.
        """
        if self.cancelled():
            raise _ProgressCancelled("Task was cancelled")
        self.send(PROGRESS, progress_info)


class ProgressBackgroundTask:
    """
    Background portion of a progress background task.

    This provides the callable that will be submitted to the worker pool, and
    sends messages to communicate with the ProgressFuture.
    """

    def __init__(self, callable, args, kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self, send, cancelled):
        progress = ProgressReporter(send=send, cancelled=cancelled)
        self.kwargs["progress"] = progress.report

        try:
            result = self.callable(*self.args, **self.kwargs)
        except _ProgressCancelled:
            pass
        else:
            send(RETURNED, result)


class ProgressFuture(BaseFuture):
    """
    Object representing the front-end handle to a ProgressBackgroundTask.
    """

    #: Event fired whenever a progress message arrives from the background.
    progress = Event(Any())

    @property
    def ok(self):
        """
        Boolean indicating whether the background job completed successfully.

        Not available for cancelled or pending jobs.
        """
        if self.state != COMPLETED:
            raise AttributeError(
                "Job has not yet completed, or was cancelled."
                "Job status is {}".format(self.state)
            )

        return self._ok

    @property
    def result(self):
        """
        Result of the background task. Raises an ``AttributeError`` on access
        if no result is available (because the background task failed, was
        cancelled, or has not yet completed).

        Note: this is deliberately a regular Python property rather than a
        Trait, to discourage users from attaching Traits listeners to
        it. Listen to the state or its derived traits instead.
        """
        if self.state != COMPLETED:
            raise AttributeError(
                "Job has not yet completed, or was cancelled. "
                "Job status is {}".format(self.state)
            )

        if not self._ok:
            raise AttributeError(
                "No result available; job raised an exception. "
                "Exception details are in the 'exception' attribute."
            )

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
        if self.state != COMPLETED:
            raise AttributeError(
                "Job has not yet completed, or was cancelled. "
                "Job status is {}".format(self.state)
            )

        if self._ok:
            raise AttributeError(
                "This job completed without raising an exception. "
                "See the 'result' attribute for the job result."
            )

        return self._exception

    # Private traits ##########################################################

    #: Boolean indicating whether we the job completed successfully.
    _ok = Bool()

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    def _process_raised(self, exception_info):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._exception = exception_info
            self._ok = False

    def _process_returned(self, result):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._result = result
            self._ok = True

    def _process_progress(self, progress_info):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self.progress = progress_info


@IJobSpecification.register
class BackgroundProgress(HasStrictTraits):
    """
    Object representing the background task to be executed.
    """

    #: The callable to be executed.
    callable = Callable()

    #: Positional arguments to be passed to the callable.
    args = Tuple()

    #: Named arguments to be passed to the callable.
    kwargs = Dict(Str(), Any())

    def background_job(self):
        """
        Return a background callable for this job specification.

        Returns
        -------
        background : callable
            Callable accepting arguments ``sender`` and ``cancelled``, and
            returning nothing. The callable will use ``sender`` to send
            messages and ``cancelled` to check whether the job has been
            cancelled.
        """
        return ProgressBackgroundTask(
            callable=self.callable, args=self.args, kwargs=self.kwargs.copy(),
        )

    def future(self, cancel, receiver):
        """
        Return a future for a background job.

        Parameters
        ----------
        cancel : callable
            Callable called with no arguments to request cancellation
            of the background task.
        receiver : MessageReceiver
            Object that remains in the main thread and receives messages sent
            by the message sender. This is a HasTraits subclass with
            a 'message' Event trait that can be listened to for arriving
            messages.

        Returns
        -------
        future : ProgressFuture
            Foreground object representing the state of the running
            calculation.
        """
        if "progress" in self.kwargs:
            raise TypeError("progress may not be passed as a named argument")

        return ProgressFuture(_cancel=cancel, _receiver=receiver)


def submit_progress(executor, callable, *args, **kwargs):
    """
    Convenience function to submit a background progress call.

    Parameters
    ----------
    executor : TraitsExecutor
        Executor to submit the call to.
    callable : callable accepting a "progress" named argument
        Function executed in the background to provide the iterable. This
        should accept a "progress" named argument. The callable can then
        call the "progress" object to report progress.
    *args
        Positional arguments to pass to that function.
    **kwargs
        Named arguments to pass to that function. These should not include
        "progress".

    Returns
    -------
    future : ProgressFuture
        Object representing the state of the background task.
    """
    task = BackgroundProgress(callable=callable, args=args, kwargs=kwargs)
    return executor.submit(task)
