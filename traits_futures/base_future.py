# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Base class providing common pieces of the Future machinery.
"""

from traits.api import (
    Any,
    Bool,
    Event,
    HasStrictTraits,
    on_trait_change,
    Property,
    provides,
    Str,
    Tuple,
)

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
from traits_futures.i_future import IFuture


@provides(IFuture)
class BaseFuture(HasStrictTraits):
    """
    Convenience base class for the various flavours of Future.
    """

    #: The state of the background task, to the best of the knowledge of
    #: this future. One of the six constants ``WAITING``, ``EXECUTING``,
    #: ``COMPLETED``, ``FAILED``, ``CANCELLING`` or ``CANCELLED``.
    state = Property(FutureState)

    #: True if cancellation of the background task can be requested, else
    #: False. Cancellation of the background task can be requested only if
    #: the future's ``state`` is either ``WAITING`` or ``EXECUTING``.
    cancellable = Property(Bool())

    #: True when communications from the background task are complete.
    #: At that point, no further state changes can occur for this future.
    #: This trait has value True if the ``state`` is one of ``COMPLETED``,
    #: ``FAILED``, or ``CANCELLED``. It's safe to listen to this trait
    #: for changes: it will always fire exactly once, and when it fires
    #: it will be consistent with the ``state``.
    done = Property(Bool())

    #: Event trait providing custom messages from the background task.
    #: Subclasses of ``BaseFuture`` can listen to this trait and interpret
    #: the messages in whatever way they like. Each message takes the
    #: form ``(message_type, message_args)``.
    message = Event(Tuple(Str(), Any()))

    @property
    def result(self):
        """
        Result of the background task.

        This attribute is only available if the state of the future is
        ``COMPLETED``. If the future has not reached the ``COMPLETED`` state,
        any attempt to access this attribute will raise an ``AttributeError``.

        Returns
        -------
        result : object
            The result obtained from the background task.

        Raises
        ------
        AttributeError
            If the task is still executing, or was cancelled, or raised an
            exception instead of returning a result.
        """
        if self._state != COMPLETED:
            raise AttributeError(
                "No result available. Task has not yet completed, "
                "or was cancelled, or failed with an exception. "
                "Task state is {}".format(self._state)
            )
        return self._result

    @property
    def exception(self):
        """
        Information about any exception raised by the background task.

        This attribute is only available if the state of this future is
        ``FAILED``. If the future has not reached the ``FAILED`` state, any
        attempt to access this attribute will raise an ``AttributeError.``

        Returns
        -------
        exc_info : tuple(str, str, str)
            Tuple containing exception information in string form:
            (exception type, exception value, formatted traceback).

        Raises
        ------
        AttributeError
            If the task is still executing, or was cancelled, or completed
            without raising an exception.
        """
        if self._state != FAILED:
            raise AttributeError(
                "No exception information available. Task has "
                "not yet completed, or was cancelled, or completed "
                "without an exception. "
                "Task state is {}".format(self.state)
            )
        return self._exception

    def cancel(self):
        """
        Request cancellation of the background task.

        A task in ``WAITING`` or ``EXECUTING`` state will immediately be moved
        to ``CANCELLING`` state. If the task is not in ``WAITING`` or
        ``EXECUTING`` state, this function will raise ``RuntimeError``.

        Raises
        ------
        RuntimeError
            If the task has already completed or cancellation has already
            been requested.
        """

        if not self.cancellable:
            raise RuntimeError(
                "Can only cancel a waiting or executing task. "
                "Task state is {}".format(self.state)
            )
        self._cancel = True
        self._user_requested_cancellation()

    @on_trait_change("message")
    def dispatch_message(self, message):
        """
        Automate dispatch of different types of message.

        This is a convenience function, and may be safely overridden by
        subclasses that want to use a different dispatch mechanism. For
        a message type ``msgtype``, it looks for a method called
        ``_process_<msgtype>`` and dispatches the message arguments to
        that method. Subclasses then only need to provide the appropriate
        ``_process_<msgtype>`` methods.

        If the future is already in CANCELLING state, no message is dispatched.
        """
        # Ignore messages that arrive after a cancellation request.
        if self._state == CANCELLING:
            return
        elif self._state == EXECUTING:
            message_type, message_arg = message
            method_name = "_process_{}".format(message_type)
            getattr(self, method_name)(message_arg)
        else:
            raise RuntimeError("Received custom message in unexpected state.")

    # Semi-private methods ####################################################

    # These methods represent the state transitions in response to external
    # events. They're used by the FutureWrapper, but are not intended for use
    # by the users of Traits Futures.

    def _task_started(self, none):
        """
        Update state when the background task has started processing.

        A future in WAITING state moves to EXECUTING. A future in CANCELLING
        state stays in CANCELLING state.
        """
        if self._state == WAITING:
            self._state = EXECUTING
        elif self._state == CANCELLING:
            self._state = CANCELLING
        else:
            raise RuntimeError("Unexpected 'started' message")

    def _task_returned(self, result):
        """
        Update state when background task reports completing successfully.

        A future in CANCELLING state moves to CANCELLED state. A future in
        EXECUTING state moves to COMPLETED state.
        """
        if self._state == EXECUTING:
            self._result = result
            self._state = COMPLETED
        elif self._state == CANCELLING:
            self._state = CANCELLED
        else:
            raise RuntimeError("Unexpected 'returned' message")

    def _task_raised(self, exception_info):
        """
        Update state when the background task reports completing with an error.

        A future in CANCELLING state moves to CANCELLED state. A future in
        EXECUTING state moves to FAILED state.
        """
        if self._state == EXECUTING:
            self._exception = exception_info
            self._state = FAILED
        elif self._state == CANCELLING:
            self._state = CANCELLED
        else:
            raise RuntimeError("Unexpected 'raised' message")

    def _user_requested_cancellation(self):
        """
        Update state when the user requests cancellation.

        A future in WAITING or EXECUTING state moves to CANCELLING state.
        """
        if self._state == WAITING:
            self._state = CANCELLING
        elif self._state == EXECUTING:
            self._state = CANCELLING
        else:
            raise RuntimeError("Unexpected 'cancel' message")

    # Private traits ##########################################################

    #: Event fired on cancellation request.
    _cancel = Event()

    #: The current state of the future.
    _state = FutureState

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    def _get_state(self):
        return self._state

    def _get_cancellable(self):
        return self._state in CANCELLABLE_STATES

    def _get_done(self):
        return self._state in DONE_STATES

    def __state_changed(self, old_state, new_state):
        self.trait_property_changed("state", old_state, new_state)

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
