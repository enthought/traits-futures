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
    CANCELLING,
    COMPLETED,
    DONE_STATES,
    FAILED,
    FutureState,
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
    state = FutureState

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
        if self.state != COMPLETED:
            raise AttributeError(
                "No result available. Task has not yet completed, "
                "or was cancelled, or failed with an exception. "
                "Task state is {}".format(self.state)
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
        if self.state != FAILED:
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

        A task in WAITING or EXECUTING state will immediately be moved to
        CANCELLING state. If the task is not in WAITING or EXECUTING state,
        this function will raise ``RuntimeError``.

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
        self.state = CANCELLING

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
        """
        message_type, message_arg = message
        method_name = "_process_{}".format(message_type)
        getattr(self, method_name)(message_arg)

    # Private traits ##########################################################

    #: Event fired on cancellation request.
    _cancel = Event()

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

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
