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
Support for an interruptible progress-reporting callable.

This module defines a task specification and a corresponding future for tasks
that execute in the background and report progress information to the
foreground. The points at which progress is reported also represent points at
which the task can be interrupted.

"""

import abc

from traits.api import Callable, Dict, HasStrictTraits, Int, Str, Tuple, Union

from traits_futures.base_future import BaseFuture, BaseTask, TaskCancelled
from traits_futures.i_task_specification import ITaskSpecification

# XXX Fix IStepsReporter to match the actual interface of the reporter.
# XXX Add NullReporter, for convenience in testing.


class IStepsReporter(abc.ABC):
    """Interface for step-reporting object passed to the background job."""

    @abc.abstractmethod
    def start(self, message=None, *, steps=None):
        """
        Set an initial message and set the total number of steps.

        Parameters
        ----------
        message : str, optional
            Message to set at start time.
        steps : int, optional
            Number of steps, if known.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """

    @abc.abstractmethod
    def step(self, message=None, *, step_size=1):
        """
        Start a processing step.

        Parameters
        ----------
        message : str, optional
            A description of this step.
        step_size : int, optional
            The size of this step (in whatever units are being used).
            Defaults to 1.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """

    @abc.abstractmethod
    def stop(self, message=None, *, ):
        """
        """


# Message types for messages sent from the background to the future.

#: Message sent on a start or step operation. Argument is a tuple
#: (step, steps, message), with:
#:
#: * step: int - number of completed steps so far
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

    def start(self, message=None, *, steps=None):
        """
        Set an initial message and set the total number of steps.

        Parameters
        ----------
        message : str, optional
            Message to set at start time.
        steps : int, optional
            Number of steps, if known.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """
        self._steps = steps
        self._message = message
        self._send(STEP, (self._step, self._steps, self._message))

    def step(self, message, *, step_size=1):
        """
        Start a processing step.

        Parameters
        ----------
        message : str, optional
            A description of this step.
        step_size : int, optional
            The size of this step (in whatever units are being used).
            Defaults to 1.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """
        self._check_cancel()

        # Close the previous step, if any.
        if self._step_size is not None:
            self._step += self._step_size
            self._step_size = None

        self._message = message
        self._step_size = step_size
        self._send(STEP, (self._step, self._steps, self._message))

    def stop(self, message="Complete"):
        self._check_cancel()

        # Close the previous step, if any.
        if self._step_size is not None:
            self._step += self._step_size
            self._step_size = None

        self._message = message
        self._send(STEP, (self._step, self._steps, self._message))

    # Private traits ##########################################################

    #: Total number of steps, if known. None if not known.
    _steps = Union(None, Int())

    #: Number of steps completed.
    _step = Int(0)

    #: Size of the step currently in progress, or None if there's no current
    #: step (because we haven't started, or have finished).
    _step_size = Union(None, Int())

    #: Description of the step currently in progress, or None.
    _message = Union(None, Str())

    #: Hook to send messages to the foreground. In normal use, this is provided
    #: by the Traits Futures machinery.
    _send = Callable()

    #: Callable to check whether the task has been cancelled, provided
    #: by the Traits Futures machinery.
    _cancelled = Callable()

    # Private methods #########################################################

    def _close(self):
        if self._step_size is not None:
            self._step += self._step_size
            self._step_size = None
            self._message = None

        self._send(STEP, (self._step, self._steps, self._message))

    def _check_cancel(self):
        """Check if the task has been cancelled.

        Raises
        ------
        TaskCancelled
            If the task has been cancelled.
        """
        if self._cancelled():
            raise TaskCancelled("Cancellation requested via the future")


class StepsTask(BaseTask):
    """
    Wrapper around the actual callable to be run.

    This wrapper handles capturing exceptions and sending the final status of
    the task on completion.
    """

    def __init__(self, callable, args, kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def run(self):
        reporter = StepsReporter(_send=self.send, _cancelled=self.cancelled)
        try:
            result = self.callable(
                *self.args,
                **self.kwargs,
                reporter=reporter,
            )
            reporter._close()
        except TaskCancelled:
            return None
        else:
            return result


class StepsFuture(BaseFuture):
    """
    Object representing the front-end handle to a background call.
    """

    #: Total number of steps, if known. None if not known.
    steps = Union(None, Int())

    #: The most recently completed step, if any.
    step = Int(0)

    #: Most recently received message from the background task.
    message = Union(None, Str())

    # Private methods #########################################################

    def _process_step(self, step_event):
        """
        Process a STEP message from the background task.
        """
        step, steps, message = step_event
        self.message = message
        self.steps = steps
        self.step = step


@ITaskSpecification.register
class BackgroundSteps(HasStrictTraits):
    """
    Object representing the background call to be executed.
    """

    #: The callable for the task.
    callable = Callable()

    #: Positional arguments to be passed to the callable.
    args = Tuple()

    #: Named arguments to be passed to the callable, excluding the "reporter"
    #: named argument. The "reporter" argument will be supplied through the
    #: execution machinery.
    kwargs = Dict(Str())

    # --- ITaskSpecification implementation -----------------------------------

    def future(self, cancel):
        """
        Return a Future for the background task.

        Parameters
        ----------
        cancel
            Zero-argument callable, returning no useful result. The returned
            future's ``cancel`` method should call this to request cancellation
            of the associated background task.

        Returns
        -------
        future : ProgressFuture
            Future object that can be used to monitor the status of the
            background task.
        """
        return StepsFuture(_cancel=cancel)

    def task(self):
        """
        Return a background callable for this task specification.

        Returns
        -------
        task : StepsTask
            Callable accepting arguments ``send`` and ``cancelled``. The
            callable can use ``send`` to send messages and ``cancelled`` to
            check whether cancellation has been requested.
        """
        return StepsTask(
            callable=self.callable,
            args=self.args,
            kwargs=self.kwargs,
        )


def submit_steps(executor, callable, *args, **kwargs):
    """
    Convenience function to submit a BackgroundSteps task to an executor.

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
        Object representing the state of the background task.
    """
    if "reporter" in kwargs:
        raise TypeError(
            "The 'reporter' parameter will be passed automatically; it "
            "should not be included in the named parameters."
        )

    return executor.submit(
        BackgroundSteps(
            callable=callable,
            args=args,
            kwargs=kwargs,
        )
    )
