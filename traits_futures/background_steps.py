# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Background task for an interruptible progress-reporting callable.

This module defines a Traits Futures task specification and a corresponding
future for tasks that execute in the background and report progress information
to the foreground. The points at which progress is reported also represent
points at which the task can be interrupted.

"""

from abc import ABC

from traits.api import (
    Callable,
    Dict,
    HasStrictTraits,
    Instance,
    Int,
    Str,
    Tuple,
)

from traits_futures.base_future import BaseFuture
from traits_futures.future_states import FAILED
from traits_futures.i_task_specification import ITaskSpecification


class StepsCancelled(Exception):
    """The user has cancelled this background task."""


class IStepsReporter(ABC):
    """Communicate progress information about a background job."""

    def start(self, message=None, steps=-1):
        """Start reporting progress.

        Parameters
        ----------
        message : str, optional
            A description for the job at the start.
        steps : int, optional
            The number of steps this job will perform. By default,
            this job has no known number of steps. Any UI
            representation will just show that work is being done
            without making any claims about quantitative progress.

        Raises
        ------
        StepsCancelled
            If the user has called ``cancel()`` before this.
        """

    def step(self, message=None, step=None, steps=None):
        """Emit a step event.

        Parameters
        ----------
        message : str, optional
            A description of what is currently being done, replacing the
            current message.
        step : int, optional
            The step number. If omitted, an internal count will be
            incremented by one.
        steps : int, optional
            The new total number of steps, if changed.

        Raises
        ------
        StepsCancelled
            If the user has called ``cancel()`` before this.
        """


# Message types for messages sent from the background to the future.

#: Message sent on a start or step operation. Argument is a tuple
#: (step, steps, message), with:
#: * step: int or None - number of completed steps so far
#: * steps: int or None - total number of steps, if known
#: * message: str or None - message to display for this step
STEP = "step"


@IStepsReporter.register
class StepsReporter(HasStrictTraits):
    """
    Object used by the background task to report progress information.

    A :class:`StepsReporter` instance is passed to the background task,
    and its ``start`` and ``step`` methods can be used by that
    background task to report progress.

    """

    def start(self, message=None, steps=-1):
        """Start reporting progress.

        Parameters
        ----------
        message : str, optional
            A description for the task at the start.
        steps : int, optional
            The number of steps this task will perform. By default,
            this task has no known number of steps. Any UI
            representation will just show that work is being done
            without making any claims about quantitative progress.

        Raises
        ------
        StepsCancelled
            If the user has called ``cancel()`` before this.
        """
        self._check_cancel()
        self._send(STEP, (0, steps, message))

    def step(self, message=None, step=None, steps=None):
        """Emit a step event.

        Parameters
        ----------
        message : str, optional
            A description of what is currently being done, replacing the
            current message.
        step : int, optional
            The step number. If omitted, an internal count will be
            incremented by one.
        steps : int, optional
            The new total number of steps, if changed.

        Raises
        ------
        StepsCancelled
            If the user has called ``cancel()`` before this.
        """
        self._check_cancel()
        self._send(STEP, (step, steps, message))

    # Private traits ##########################################################

    #: Hook to send messages to the foreground. In normal use, this is provided
    #: by the Traits Futures machinery.
    _send = Callable()

    #: Callable to check whether the task has been cancelled, provided
    #: by the Traits Futures machinery.
    _cancelled = Callable()

    # Private methods #########################################################

    def _check_cancel(self):
        """Check if the task has been cancelled.

        Raises
        ------
        StepsCancelled
            If the task has been cancelled.
        """
        if self._cancelled():
            raise StepsCancelled("Cancellation requested via the future")


class StepsBackgroundTask:
    """
    Wrapper around the actual callable to be run.

    This wrapper handles capturing exceptions and sending the final status of
    the task on completion.
    """

    def __init__(self, callable, args, kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self, send, cancelled):
        progress = StepsReporter(_send=send, _cancelled=cancelled)
        try:
            result = self.callable(
                *self.args, **self.kwargs, progress=progress
            )
        except StepsCancelled:
            return None
        else:
            return result


class StepsFuture(BaseFuture):
    """
    Object representing the front-end handle to a background call.
    """

    #: Total number of steps.
    #: A value of -1 implies that the number of steps is unknown.
    steps = Int(-1)

    #: The most recently completed step.
    step = Int(0)

    #: Most recently received message from either the background task
    #: or from cancellation.
    message = Str()

    @property
    def error(self):
        """
        The exception raised by the background task, if any.

        This attribute is only available if the state of this future is
        ``FAILED``. If the future has not reached the ``FAILED`` state, any
        attempt to access this attribute will raise an ``AttributeError.``

        Returns
        -------
        exception: BaseException
            The exception object raised by the background task.

        Raises
        ------
        AttributeError
            If the task is still executing, or was cancelled, or completed
            without raising an exception.
        """
        if self.state != FAILED:
            raise AttributeError(
                "No exception information available. Task has "
                "not yet completed, or was cancelled, or completed "
                "without an exception. "
                "Task state is {}".format(self.state)
            )
        return self._error

    # Private traits ##########################################################

    #: Any exception raised by the background task.
    _error = Instance(BaseException, allow_none=True)

    # Private methods #########################################################

    def _process_step(self, step_event):
        """
        Process a STEP message from the background task.
        """
        step, steps, message = step_event
        if message is not None:
            self.message = message
        if steps is not None:
            self.steps = steps
        if step is None:
            self.step += 1
        else:
            self.step = step

    def _process_error(self, error):
        """
        Process an ERROR message from the background task.
        """
        self._error = error


@ITaskSpecification.register
class BackgroundSteps(HasStrictTraits):
    """
    Object representing the background call to be executed.

    The *callable* function will be called with an additional
    argument, passed via the name "progress". The object passed
    can then be used to submit progress information to the foreground.

    Parameters
    ----------
    callable : callable
        The callable to be executed in the background.
    args : tuple
        Positional arguments to be passed to *callable*.
    kwargs : mapping
        Keyword arguments to be passed to *callable*.
    """

    #: The callable for the task.
    callable = Callable()

    #: Positional arguments to be passed to the callable.
    args = Tuple()

    #: Named arguments to be passed to the callable, excluding the "progress"
    #: named argument. The "progress" argument will be supplied through the
    #: execution machinery.
    kwargs = Dict(Str())

    # --- ITaskSpecification implementation -----------------------------------

    def future(self):
        """
        Return a Future for the background task.

        Returns
        -------
        future : ProgressFuture
            Future object that can be used to monitor the status of the
            background task.
        """
        return StepsFuture()

    def background_task(self):
        """
        Return a background callable for this task specification.

        Returns
        -------
        collections.abc.Callable
            Callable accepting arguments ``send`` and ``cancelled``. The
            callable can use ``send`` to send messages and ``cancelled`` to
            check whether cancellation has been requested.
        """
        return StepsBackgroundTask(
            callable=self.callable,
            args=self.args,
            kwargs=self.kwargs.copy(),
        )


def submit_steps(executor, callable, *args, **kwargs):
    """
    Convenience function to submit a background progress task to an executor.

    Parameters
    ----------
    executor : TraitsExecutor
        Executor to submit the task to.
    callable : collections.abc.Callable
        Callable to execute in the background. This should accept a
        "progress" keyword argument, in addition to any other positional
        and named arguments it needs. When the callable is invoked, an
        instance of "StepsReporter" will be supplied via that "progress"
        argument.
    *args
        Positional arguments to pass to the callable.
    **kwargs
        Named arguments to pass to the callable, excluding the "progress"
        argument. That argument will be passed separately.

    Returns
    -------
    future : StepsFuture
        Object representing the state of the background call.
    """
    return executor.submit(
        BackgroundSteps(
            callable=callable,
            args=args,
            kwargs=kwargs,
        )
    )
