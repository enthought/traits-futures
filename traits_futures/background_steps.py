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
    Union,
)

from traits_futures.base_future import BaseFuture, BaseTask, TaskCancelled
from traits_futures.i_task_specification import ITaskSpecification

# XXX Add NullReporter, for convenience in testing progress-reporting tasks
#     - later?
# XXX Add "check" method to just check for cancellation - later?


#: Tuple encapsulating the entire progress state of the task.
StepsState = collections.namedtuple(
    "StepsState", ["total", "complete", "pending", "message"]
)


class IStepsReporter(abc.ABC):
    """Interface for step-reporting object passed to the background job."""

    @abc.abstractmethod
    def start(self, message=None, *, total=None):
        """
        Set an initial message and set the progress total.

        Parameters
        ----------
        message : str, optional
            Message to set at start time.
        total : int, optional
            Total progress, in whatever units makes sense for the application.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """

    @abc.abstractmethod
    def step(self, message=None, *, size=1):
        """
        Start a processing step.

        Parameters
        ----------
        message : str, optional
            A description of this step.
        size : int, optional
            The size of this step (in whatever units make sense for the
            application at hand). Defaults to 1.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """

    @abc.abstractmethod
    def stop(self, message=None):
        """
        Report that processing is complete.

        Also updates the total progress, if any tasks are pending.

        Parameters
        ----------
        message : str, optional
            Message to display on completion. For a progress dialog that
            disappears on completion, this message will never be seen by
            the user, but for other views the message may be visible.
        """


# Message types for messages sent from the background to the future.

#: Message sent on a start or step operation. Argument is an instance
#: of StepsState.
UPDATE = "update"


@IStepsReporter.register
class StepsReporter:
    """
    Object used by the background task to report progress information.

    A :class:`StepsReporter` instance is passed to the background task,
    and its ``start`` and ``step`` methods can be used by that
    background task to report progress.

    """

    def __init__(self, send, cancelled, initial_steps_state):
        #: Callable used to send messages to the linked future.
        self._send = send

        #: Callable used to check for task cancellation.
        self._cancelled = cancelled

        #: Progress state.
        self._steps_state = initial_steps_state

    def start(self, message=None, *, total=None):
        """
        Set an initial message and set the progress total.

        Parameters
        ----------
        message : str, optional
            Message to set at start time.
        total : int, optional
            Total progress, in whatever units makes sense for the application.

        Raises
        ------
        TaskCancelled
            If the user has called ``cancel()`` before this.
        """
        self._check_cancel()

        self._steps_state = self._steps_state._replace(
            total=self._steps_state.total if total is None else total,
            message=self._steps_state.message if message is None else message,
        )
        self._report_state()

    def step(self, message=None, *, size=1):
        """
        Start a processing step.

        Parameters
        ----------
        message : str, optional
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

        self._steps_state = self._steps_state._replace(
            complete=self._steps_state.complete + self._steps_state.pending,
            pending=size,
            message=self._steps_state.message if message is None else message,
        )

        self._report_state()

    def stop(self, message=None):
        """
        Report that processing is complete.

        Also updates the total progress, if any tasks are pending.

        Parameters
        ----------
        message : str, optional
            Message to display on completion. For a progress dialog that
            disappears on completion, this message will never be seen by
            the user, but for other views the message may be visible.
        """
        self._check_cancel()

        self._steps_state = self._steps_state._replace(
            complete=self._steps_state.complete + self._steps_state.pending,
            pending=0,
            message=self._steps_state.message if message is None else message,
        )
        self._report_state()

    # Private methods and properties ##########################################

    def _close(self):
        if self._steps_state.pending:
            self._steps_state = StepsState(
                total=self._steps_state.total,
                complete=self._steps_state.complete
                + self._steps_state.pending,
                pending=0,
                message=self._steps_state.message,
            )

            self._report_state()

    def _report_state(self):
        self._send(UPDATE, self._steps_state)

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

    def __init__(self, initial_steps_state, callable, args, kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.initial_steps_state = initial_steps_state

    def run(self):
        reporter = StepsReporter(
            send=self.send,
            cancelled=self.cancelled,
            initial_steps_state=self.initial_steps_state,
        )
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
    Object representing the front-end handle to a background steps task.
    """

    #: Most recently received message from the background task.
    message = Property(Union(None, Str()))

    #: Total work, in whatever units make sense for the application.
    total = Property(Union(None, Int()))

    #: Units of work completed so far.
    complete = Property(Int())

    # Private traits ##########################################################

    #: The progress state of the background task.
    _steps_state = Instance(StepsState, allow_none=False)

    # Private methods #########################################################

    def _process_update(self, steps_state):
        """
        Process an UPDATE message from the background task.
        """
        self._steps_state = steps_state

    def _get_message(self):
        return self._steps_state.message

    def _get_total(self):
        return self._steps_state.total

    def _get_complete(self):
        return self._steps_state.complete

    @observe("_steps_state")
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
    total = Union(None, Int())

    #: Initial message.
    message = Union(None, Str())

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
            _steps_state=self._initial_steps_state,
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
            initial_steps_state=self._initial_steps_state,
            callable=self.callable,
            args=self.args,
            kwargs=self.kwargs,
        )

    # Private methods #########################################################

    @property
    def _initial_steps_state(self):
        return StepsState(
            total=self.total,
            complete=0,
            pending=0,
            message=self.message,
        )


def submit_steps(executor, total, message, callable, *args, **kwargs):
    """
    Convenience function to submit a BackgroundSteps task to an executor.

    Note: the 'executor', 'total', 'message', and 'callable' parameters should
    be treated as positional only, and should always be passed by position
    instead of by name. Future versions of the library may enforce this
    restriction.

    Parameters
    ----------
    executor : TraitsExecutor
        Executor to submit the task to.
    total : int or None
        Total units of work for this task, if known.
    message : str or None
        Initial message.
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
