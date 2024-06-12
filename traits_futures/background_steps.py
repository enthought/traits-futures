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
import collections

from traits.api import (
    Callable,
    Dict,
    HasStrictTraits,
    Instance,
    Int,
    observe,
    Property,
    Str,
    Tuple,
)

from traits_futures.base_future import BaseFuture, BaseTask, TaskCancelled
from traits_futures.i_task_specification import ITaskSpecification


class IStepsReporter(abc.ABC):
    """
    Interface for progress reporters.

    This is the interface that's implemented by the StepsReporter
    object that's passed to the background tasks.
    """

    @abc.abstractmethod
    def step(self, message, *, size=1):
        """
        Start a processing step.

        Parameters
        ----------
        message : str
            A description of this step.
        size : int, optional
            The size of this step, in whatever units make sense for the
            application at hand. Defaults to 1.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """

    @abc.abstractmethod
    def stop(self, message):
        """
        Report that processing is complete.

        Also updates the total progress, if any tasks are pending.

        Parameters
        ----------
        message : str
            Message to display on completion. For a progress dialog that
            disappears on completion, this message will never be seen by
            the user, but for other views the message may be visible.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """


class StepsState(
    collections.namedtuple(
        "StepsState", ["total", "complete", "pending", "message"]
    )
):
    """
    Tuple subclass encapsulating progress state of the task.

    Objects of this type capture the progress state of an in-progress task.

    Attributes
    ----------
    total : int
        Total number of units of work for the task.
    complete : int
        Total units of work completed.
    pending : int
        Size of the step currently in progress, or 0 if there's no
        in-progress step.
    message : str
        Description of the current step, or a more general message
        if processing has completed or has yet to start.
    """

    @classmethod
    def initial(cls, total, message):
        """
        Initial state, given total work and initial message.

        Parameters
        ----------
        total : int
            Total units of work.
        message : str
            Message to use for the initial state.

        Returns
        -------
        StepsState
        """
        return cls(total=total, complete=0, pending=0, message=message)

    def set_message(self, message):
        """
        Return a copy of this state with an updated message.

        Parameters
        ----------
        message : str
            Message to use for the new state.

        Returns
        -------
        StepsState
        """
        return self._replace(message=message)

    def set_step(self, size):
        """
        Return a copy of this state updated for the next processing step.

        Parameters
        ----------
        size : int
            Number of units of work represented by the next step.

        Returns
        -------
        StepsState
        """
        return self._replace(
            complete=self.complete + self.pending,
            pending=size,
        )


#: Message type for the message sent on each state update. The argument is an
#: instance of StepsState.
UPDATE = "update"


@IStepsReporter.register
class StepsReporter:
    """
    Object used by the background task to report progress information.

    A :class:`StepsReporter` instance is passed to the background task, and its
    ``step`` and ``stop`` methods can be used by that background task to report
    progress.

    Parameters
    ----------
    send
        Callable provided by the Traits Futures machinery, and used to send
        messages to the linked future.
    cancelled
        Callable provided by the Traits Futures machinery, and used to check
        for cancellation requests.
    state : StepsState
        Initial state of the reporter.
    """

    def __init__(self, send, cancelled, state):
        self._send = send
        self._cancelled = cancelled
        self._state = state

    def step(self, message, *, size=1):
        """
        Start a processing step.

        Parameters
        ----------
        message : str
            A description of this step.
        size : int, optional
            The size of this step (in whatever units make sense for the
            application at hand). Defaults to 1.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """
        self._check_cancel()
        self._state = self._state.set_step(size).set_message(message)
        self._send(UPDATE, self._state)

    def stop(self, message):
        """
        Report that processing is complete.

        Also updates the total progress, if any tasks are pending.

        Parameters
        ----------
        message : str
            Message to display on completion. For a progress dialog that
            disappears on completion, this message will never be seen by
            the user, but for other views the message may be visible.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """
        self._check_cancel()
        self._state = self._state.set_step(0).set_message(message)
        self._send(UPDATE, self._state)

    # Private methods and properties ##########################################

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

    Parameters
    ----------
    initial_state : StepsState
        Initial state of the progress.
    callable
        User-supplied function to be called.
    args : tuple
        Positional arguments to be passed to ``callable``.
    kwargs : dict
        Named arguments to be passed to ``callable``, not including the
        ``reporter`` argument.
    """

    def __init__(self, initial_state, callable, args, kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.initial_state = initial_state

    def run(self):
        """
        Run the body of the steps task.

        Returns
        -------
        object
            May return any object. That object will be delivered to the
            future's ``result`` attribute.
        """
        reporter = StepsReporter(
            send=self.send,
            cancelled=self.cancelled,
            state=self.initial_state,
        )
        try:
            result = self.callable(
                *self.args,
                **self.kwargs,
                reporter=reporter,
            )
        except TaskCancelled:
            return None
        else:
            return result


class StepsFuture(BaseFuture):
    """
    Object representing the front-end handle to a background steps task.
    """

    #: Most recently received message from the background task.
    message = Property(Str())

    #: Total work, in whatever units make sense for the application.
    total = Property(Int())

    #: Units of work completed so far.
    complete = Property(Int())

    # Private traits ##########################################################

    #: The progress state of the background task.
    _progress_state = Instance(StepsState, allow_none=False)

    # Private methods #########################################################

    def _process_update(self, progress_state):
        """
        Process an UPDATE message from the background task.
        """
        self._progress_state = progress_state

    def _get_message(self):
        """Traits property getter for the 'message' trait."""
        return self._progress_state.message

    def _get_total(self):
        """Traits property getter for the 'total' trait."""
        return self._progress_state.total

    def _get_complete(self):
        """Traits property getter for the 'complete' property."""
        return self._progress_state.complete

    @observe("_progress_state")
    def _update_state_traits(self, event):
        if event.old is None:
            return

        old_state, new_state = event.old, event.new

        if old_state.message != new_state.message:
            self.trait_property_changed(
                "message", old_state.message, new_state.message
            )
        if old_state.total != new_state.total:
            self.trait_property_changed(
                "total", old_state.total, new_state.total
            )
        if old_state.complete != new_state.complete:
            self.trait_property_changed(
                "complete", old_state.complete, new_state.complete
            )


@ITaskSpecification.register
class BackgroundSteps(HasStrictTraits):
    """
    Object representing the background task to be executed.
    """

    #: Total units of work for the task, if known. None if not known.
    total = Int()

    #: Initial message.
    message = Str()

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
        return StepsFuture(
            _cancel=cancel,
            _progress_state=self._initial_state,
        )

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
            initial_state=self._initial_state,
            callable=self.callable,
            args=self.args,
            kwargs=self.kwargs,
        )

    # Private traits and methods ##############################################

    #: Initial progress state to be passed to both the task and the future.
    _initial_state = Property(
        Instance(StepsState), observe=["total", "message"]
    )

    def _get__initial_state(self):
        """Traits property getter for the _initial_state trait."""
        return StepsState.initial(total=self.total, message=self.message)


def submit_steps(executor, total, message, callable, *args, **kwargs):
    """
    Convenience function to submit a BackgroundSteps task to an executor.

    Note: the 'executor', 'total', 'message', and 'callable' parameters should
    always be passed by position instead of by name. Future versions of the
    library may enforce this restriction.

    Parameters
    ----------
    executor : TraitsExecutor
        Executor to submit the task to.
    total : int
        Total units of work for this task, in whatever units are appropriate
        for the task in hand.
    message : str
        Description of the task. This will be used until the first step
        message is received from the background task.
    callable : collections.abc.Callable
        Callable to execute in the background. This should accept a
        "reporter" keyword argument, in addition to any other positional
        and named arguments it needs. When the callable is invoked, an
        instance of "StepsReporter" will be supplied via that "reporter"
        argument.
    *args
        Positional arguments to pass to the callable.
    **kwargs
        Named arguments to pass to the callable, excluding the "reporter"
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
            total=total,
            message=message,
            callable=callable,
            args=args,
            kwargs=kwargs,
        )
    )
