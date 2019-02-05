# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Background task consisting of a simple callable.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits.api import (
    Any, Bool, Callable, Dict, Event, HasStrictTraits, HasTraits, Instance,
    on_trait_change, Property, Str, Tuple, Unicode)

from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLED, CANCELLING, EXECUTING, FAILED, COMPLETED, WAITING,
    CANCELLABLE_STATES, DONE_STATES, FutureState)

# Message types for messages from CallBackgroundTask to CallFuture.
# The background task will emit exactly one of the following
# sequences of message types:
#
#   [INTERRUPTED]
#   [STARTED, RAISED]
#   [STARTED, RETURNED]

#: Call was cancelled before it started. No arguments.
INTERRUPTED = "interrupted"

#: Call started executing. No arguments.
STARTED = "started"

#: Call failed with an exception. Argument gives exception information.
RAISED = "raised"

#: Call succeeded and returned a result. Argument is the result.
RETURNED = "returned"


class CallBackgroundTask(object):
    """
    Wrapper around the actual callable to be run. This wrapper provides the
    task that will be submitted to the concurrent.futures executor
    """
    def __init__(self, callable, args, kwargs, message_sender, cancel_event):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.message_sender = message_sender
        self.cancel_event = cancel_event

    def __call__(self):
        with self.message_sender:
            if self.cancel_event.is_set():
                self.send(INTERRUPTED)
                return

            self.send(STARTED)
            try:
                result = self.callable(*self.args, **self.kwargs)
            except BaseException as e:
                self.send(RAISED, marshal_exception(e))
                del e
            else:
                self.send(RETURNED, result)

    def send(self, message_type, message_args=None):
        """
        Send a message to the linked CallFuture.

        Sends a pair consisting of a string giving the message type
        along with an object providing any relevant arguments. The
        interpretation of the arguments depends on the message type.

        Parameters
        ----------
        message_type : string
            Type of the message to be sent.
        message_args : object, optional
            Any arguments relevant to the message.  Ideally, should be
            pickleable and immutable. If not provided, ``None`` is sent.
        """
        self.message_sender.send((message_type, message_args))


# CallFuture states. These represent the future's current
# state of knowledge of the background task. A task starts out
# in WAITING state and ends in one of the three final states:
# COMPLETED, FAILED, OR CANCELLED. The possible progressions of states are:
#
# WAITING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> FAILED
# WAITING -> EXECUTING -> COMPLETED


class CallFuture(HasStrictTraits):
    """
    Object representing the front-end handle to a background call.
    """
    #: The state of the background call, to the best of the knowledge of
    #: this future.
    state = FutureState

    #: True if this task can be cancelled, else False.
    cancellable = Property(Bool())

    #: True if we've received the final message from the background task,
    #: else False. `True` indicates either that the background task
    #: succeeded, or that it raised, or that it was cancelled.
    done = Property(Bool())

    @property
    def result(self):
        """
        Result of the background call. Raises an ``Attributerror`` on access if
        no result is available (because the background call failed, was
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
            raise RuntimeError("Can only cancel a queued or executing task.")
        self._cancel_event.set()
        self.state = CANCELLING

    # Private traits ##########################################################

    #: Private event used to request cancellation of this task. Users
    #: should call the cancel() method instead of using this event.
    _cancel_event = Any()

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Unicode(), Unicode(), Unicode())

    #: Object that receives messages from the background task.
    _message_receiver = Instance(HasTraits)

    #: Event fired when the background task is on the point of exiting.
    #: This is mostly used for internal bookkeeping.
    _exiting = Event()

    # Private methods #########################################################

    @on_trait_change('_message_receiver:done')
    def _send_exiting_event(self):
        self._exiting = True

    @on_trait_change('_message_receiver:message')
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

    def _get_cancellable(self):
        return self.state in CANCELLABLE_STATES

    def _get_done(self):
        return self.state in DONE_STATES

    def _state_changed(self, old_state, new_state):
        old_cancellable = old_state in CANCELLABLE_STATES
        new_cancellable = new_state in CANCELLABLE_STATES
        if old_cancellable != new_cancellable:
            self.trait_property_changed(
                "cancellable", old_cancellable, new_cancellable)

        old_done = old_state in DONE_STATES
        new_done = new_state in DONE_STATES
        if old_done != new_done:
            self.trait_property_changed("done", old_done, new_done)


class BackgroundCall(HasStrictTraits):
    """
    Object representing the background call to be executed.
    """
    #: The callable to be executed.
    callable = Callable()

    #: Positional arguments to be passed to the callable.
    args = Tuple()

    #: Named arguments to be passed to the callable.
    kwargs = Dict(Str(), Any())

    def future_and_callable(
            self, cancel_event, message_sender, message_receiver):
        """
        Return a future and a linked background callable.

        Parameters
        ----------
        cancel_event : threading.Event
            Event used to request cancellation of the background job.
        message_sender : MessageSender
            Object used by the background job to send messages to the
            UI. Supports the context manager protocol, and provides a
            'send' method.
        message_receiver : MessageReceiver
            Object that remains in the main thread and receives messages sent
            by the message sender. This is a HasTraits subclass with
            a 'message' Event trait that can be listened to for arriving
            messages.

        Returns
        -------
        future : CallFuture
            Foreground object representing the state of the running
            calculation.
        runner : CallBackgroundTask
            Callable to be executed in the background.
        """
        future = CallFuture(
            _cancel_event=cancel_event,
            _message_receiver=message_receiver,
        )
        runner = CallBackgroundTask(
            callable=self.callable,
            args=self.args,
            # Convert TraitsDict to a regular dict
            kwargs=dict(self.kwargs),
            message_sender=message_sender,
            cancel_event=cancel_event,
        )
        return future, runner
