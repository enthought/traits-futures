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
from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLING,
    DONE,
    WAITING,
)
from traits_futures.i_job_specification import IJobSpecification


# Message types for messages from ProgressBackgroundTask
# to ProgressFuture.

#: Task failed with an exception. Argument gives exception information.
RAISED = "raised"

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
        except BaseException as e:
            send(RAISED, marshal_exception(e))
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
        if self.state != DONE:
            raise AttributeError(
                "Background job was cancelled, or has not yet completed."
            )
        return not self._have_exception

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
        if not self._have_result:
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
        if not self._have_exception:
            raise AttributeError("No exception has been raised for this call.")
        return self._exception

    # Private traits ##########################################################

    #: Boolean indicating whether we have a result available.
    _have_result = Bool(False)

    #: Result from the background task.
    _result = Any()

    #: Boolean indicating whether we have exception information available.
    _have_exception = Bool(False)

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    def _process_raised(self, exception_info):
        assert self.state in (WAITING, CANCELLING)
        if self.state == WAITING:
            self._have_exception = True
            self._exception = exception_info

    def _process_returned(self, result):
        assert self.state in (WAITING, CANCELLING)
        if self.state == WAITING:
            self._have_result = True
            self._result = result

    def _process_progress(self, progress_info):
        assert self.state in (WAITING, CANCELLING)
        if self.state == WAITING:
            self.progress = progress_info

    def _process_started(self, none):
        # Short-circuit base class behaviour
        # XXX Remove me once the base class method is gone.
        pass


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
            callable=self.callable,
            args=self.args,
            # Convert TraitsDict to a regular dict
            kwargs=dict(self.kwargs),
        )

    def future(self, cancel, message_receiver):
        """
        Return a future for a background job.

        Parameters
        ----------
        cancel : callable
            Callable called with no arguments to request cancellation
            of the background task.
        message_receiver : MessageReceiver
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

        return ProgressFuture(
            _cancel=cancel, _message_receiver=message_receiver,
        )
