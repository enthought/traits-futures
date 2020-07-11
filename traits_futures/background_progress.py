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
    Callable,
    Dict,
    Event,
    HasStrictTraits,
    Str,
    Tuple,
)

from traits_futures.base_future import BaseFuture
from traits_futures.future_states import CANCELLING
from traits_futures.i_task_specification import ITaskSpecification


# Message types for messages from ProgressBackgroundTask
# to ProgressFuture.

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
            return self.callable(*self.args, **self.kwargs)
        except _ProgressCancelled:
            return None


class ProgressFuture(BaseFuture):
    """
    Object representing the front-end handle to a ProgressBackgroundTask.
    """

    #: Event fired whenever a progress message arrives from the background.
    progress = Event(Any())

    # Private methods #########################################################

    def _process_progress(self, progress_info):
        # Ignore progress messages that arrive after a cancellation request.
        if self.state == CANCELLING:
            return
        self.progress = progress_info


@ITaskSpecification.register
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

    #: Factory for futures.
    future = ProgressFuture

    def background_task(self):
        """
        Return a background callable for this task specification.

        Returns
        -------
        background : callable
            Callable accepting arguments ``send`` and ``cancelled``. The
            callable can use ``send`` to send messages and ``cancelled` to
            check whether cancellation has been requested.
        """
        if "progress" in self.kwargs:
            raise TypeError("progress may not be passed as a named argument")

        return ProgressBackgroundTask(
            callable=self.callable, args=self.args, kwargs=self.kwargs.copy(),
        )


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
