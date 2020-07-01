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
    HasTraits,
    Instance,
    on_trait_change,
    Property,
    Str,
    Tuple,
)

from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLABLE_STATES,
    CANCELLED,
    CANCELLING,
    COMPLETED,
    DONE_STATES,
    EXECUTING,
    FAILED,
    FutureState,
    WAITING,
)


# Message types for messages from ProgressBackgroundTask
# to ProgressFuture.

#: Task was cancelled before it started. No arguments.
INTERRUPTED = "interrupted"

#: Task started executing. No arguments.
STARTED = "started"

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

    def __init__(self, send, cancel_event):
        self.send = send
        self.cancel_event = cancel_event

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
        if self.cancel_event.is_set():
            raise _ProgressCancelled("Task was cancelled")
        self.send(PROGRESS, progress_info)


class ProgressBackgroundTask:
    """
    Background portion of a progress background task.

    This provides the callable that will be submitted to the worker pool, and
    sends messages to communicate with the ProgressFuture.
    """

    def __init__(self, callable, args, kwargs, cancel_event):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.cancel_event = cancel_event

    def __call__(self, send):
        progress = ProgressReporter(send=send, cancel_event=self.cancel_event)
        self.kwargs["progress"] = progress.report

        if self.cancel_event.is_set():
            send(INTERRUPTED)
            return

        send(STARTED)
        try:
            result = self.callable(*self.args, **self.kwargs)
        except _ProgressCancelled:
            send(INTERRUPTED)
        except BaseException as e:
            send(RAISED, marshal_exception(e))
        else:
            send(RETURNED, result)


class ProgressFuture(HasStrictTraits):
    """
    Object representing the front-end handle to a ProgressBackgroundTask.
    """

    #: The state of the background task, to the best of the knowledge of
    #: this future.
    state = FutureState

    #: True if this task can be cancelled, else False.
    cancellable = Property(Bool())

    #: True if we've received the final message from the background task,
    #: else False. `True` indicates either that the background task
    #: succeeded, or that it raised, or that it was cancelled.
    done = Property(Bool())

    #: Event fired whenever a progress message arrives from the background.
    progress = Event(Any())

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
        if self.state != FAILED:
            raise AttributeError("No exception has been raised for this call.")
        return self._exception

    def cancel(self):
        """
        Method that can be called from the main thread to
        indicate that the task should be cancelled (provided
        it hasn't already started running).
        """
        # In the interests of catching coding errors early in client
        # code, we're strict about what states we allow cancellation
        # from. Some applications may want to weaken the error below
        # to a warning, or just do nothing on an invalid cancellation.
        if not self.cancellable:
            raise RuntimeError(
                "Can only cancel a queued or executing task. "
                "Task state is {!r}".format(self.state)
            )
        self._cancel_event.set()
        self.state = CANCELLING

    # Private traits ##########################################################

    #: Private event used to request cancellation of this task. Users
    #: should call the cancel() method instead of using this event.
    _cancel_event = Any()

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    #: Object that receives messages from the background task.
    _message_receiver = Instance(HasTraits)

    # Private methods #########################################################

    @on_trait_change("_message_receiver:message")
    def _process_message(self, message):
        message_type, message_arg = message
        method_name = "_process_{}".format(message_type)
        getattr(self, method_name)(message_arg)

    def _process_interrupted(self, none):
        assert self.state in (CANCELLING,)
        self.state = CANCELLED

    def _process_started(self, none):
        assert self.state in (WAITING, CANCELLING)
        if self.state == WAITING:
            self.state = EXECUTING

    def _process_raised(self, exception_info):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._exception = exception_info
            self.state = FAILED
        else:
            self.state = CANCELLED

    def _process_returned(self, result):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._result = result
            self.state = COMPLETED
        else:
            self.state = CANCELLED

    def _process_progress(self, progress_info):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self.progress = progress_info

    def _get_cancellable(self):
        return self.state in CANCELLABLE_STATES

    def _get_done(self):
        return self.state in DONE_STATES

    def _state_changed(self, old_state, new_state):
        old_cancellable = old_state in CANCELLABLE_STATES
        new_cancellable = new_state in CANCELLABLE_STATES
        if old_cancellable != new_cancellable:
            self.trait_property_changed(
                "cancellable", old_cancellable, new_cancellable
            )

        old_done = old_state in DONE_STATES
        new_done = new_state in DONE_STATES
        if old_done != new_done:
            self.trait_property_changed("done", old_done, new_done)


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

    def future_and_callable(self, cancel_event, message_receiver):
        """
        Return a future and a linked background callable.

        Parameters
        ----------
        cancel_event : threading.Event
            Event used to request cancellation of the background task.
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
        runner : ProgressBackgroundTask
            Callable to be executed in the background.
        """
        if "progress" in self.kwargs:
            raise TypeError("progress may not be passed as a named argument")

        future = ProgressFuture(
            _cancel_event=cancel_event, _message_receiver=message_receiver,
        )
        runner = ProgressBackgroundTask(
            callable=self.callable,
            args=self.args,
            # Convert TraitsDict to a regular dict
            kwargs=dict(self.kwargs),
            cancel_event=cancel_event,
        )
        return future, runner
