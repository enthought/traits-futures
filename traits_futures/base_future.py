# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Base class providing common pieces of the Future machinery.
"""

from traits.api import (
    Any,
    Bool,
    Callable,
    Enum,
    HasStrictTraits,
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


# The BaseFuture class maintains an internal state. That internal state maps to
# the user-facing state, but is more fine grained, allowing-the class to keep
# track of the internal consistency and invariants. For example, the
# user-facing CANCELLING state doesn't indicate whether the task has started
# or not; if it *has* already started, then a "start" message from the
# background task is invalid; otherwise, it's valid. So we split this into
# two internal states: _CANCELLING_BEFORE_STARTED and _CANCELLING_AFTER_STARTED
# to allow us to detect an invalid _task_started call.


#: Internal state: initial state, not yet initialized by the executor.
_NOT_INITIALIZED = "not_initialized"

#: Internal state: initialized by the executor, waiting for the task to start.
_INITIALIZED = "initialized"

#: Internal state attained when cancellation is requested before the task
#: starts.
_CANCELLING_BEFORE_STARTED = "cancelling_before_started"

#: Internal state attained when cancellation is requested after the task
#: starts.
_CANCELLING_AFTER_STARTED = "cancelling_after_started"

#: Mapping from each internal state to the corresponding user-visible state.
_INTERNAL_STATE_TO_STATE = {
    _NOT_INITIALIZED: WAITING,
    _INITIALIZED: WAITING,
    EXECUTING: EXECUTING,
    COMPLETED: COMPLETED,
    FAILED: FAILED,
    _CANCELLING_BEFORE_STARTED: CANCELLING,
    _CANCELLING_AFTER_STARTED: CANCELLING,
    CANCELLED: CANCELLED,
}

#: Internal states corresponding to completed futures.
_DONE_INTERNAL_STATES = {
    internal_state
    for internal_state, state in _INTERNAL_STATE_TO_STATE.items()
    if state in DONE_STATES
}

#: Internal states corresponding to cancellable futures.
_CANCELLABLE_INTERNAL_STATES = {
    internal_state
    for internal_state, state in _INTERNAL_STATE_TO_STATE.items()
    if state in CANCELLABLE_STATES
}


class _StateTransitionError(Exception):
    """
    Exception used to indicate a bad state transition.

    Users should never see this exception. It indicates an error in the
    sequence of operations received by the future from the background
    task, from the executor, or from the user.
    """


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
    #: its value will be consistent with that of the ``state`` trait.
    done = Property(Bool())

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
        self._user_cancelled()

    # Semi-private methods ####################################################

    # These methods represent the state transitions in response to external
    # events. They're used by the FutureWrapper, and are potentially useful for
    # unit testing, but are not intended for use by the users of Traits
    # Futures.

    def _dispatch_message(self, message):
        """
        Automate dispatch of different types of message.

        This is a convenience function, and may be safely overridden by
        subclasses that want to use a different dispatch mechanism. For
        a message type ``msgtype``, it looks for a method called
        ``_process_<msgtype>`` and dispatches the message arguments to
        that method. Subclasses then only need to provide the appropriate
        ``_process_<msgtype>`` methods.

        If the future is already in ``CANCELLING`` state, no message is
        dispatched.

        Parameters
        ----------
        message : tuple(str, object)
            Message from the background task, in the form (message_type,
            message_args).
        """

        if self._internal_state == _CANCELLING_AFTER_STARTED:
            # Ignore messages that arrive after a cancellation request.
            return
        elif self._internal_state == EXECUTING:
            message_type, message_arg = message
            method_name = "_process_{}".format(message_type)
            getattr(self, method_name)(message_arg)
        else:
            raise _StateTransitionError(
                "Unexpected custom message in internal state {!r}".format(
                    self._internal_state
                )
            )

    def _task_started(self, none):
        """
        Update state when the background task has started processing.

        Parameters
        ----------
        none : NoneType
            This parameter is unused.
        """
        if self._internal_state == _INITIALIZED:
            self._internal_state = EXECUTING
        elif self._internal_state == _CANCELLING_BEFORE_STARTED:
            self._internal_state = _CANCELLING_AFTER_STARTED
        else:
            raise _StateTransitionError(
                "Unexpected 'started' message in internal state {!r}".format(
                    self._internal_state
                )
            )

    def _task_returned(self, result):
        """
        Update state when background task reports completing successfully.

        Parameters
        ----------
        result : any
            The object returned by the background task.
        """
        if self._internal_state == EXECUTING:
            self._cancel = None
            self._result = result
            self._internal_state = COMPLETED
        elif self._internal_state == _CANCELLING_AFTER_STARTED:
            self._internal_state = CANCELLED
        else:
            raise _StateTransitionError(
                "Unexpected 'returned' message in internal state {!r}".format(
                    self._internal_state
                )
            )

    def _task_raised(self, exception_info):
        """
        Update state when the background task reports completing with an error.

        Parameters
        ----------
        exception_info : tuple(str, str, str)
            Tuple containing exception information in string form:
            (exception type, exception value, formatted traceback).
        """
        if self._internal_state == EXECUTING:
            self._cancel = None
            self._exception = exception_info
            self._internal_state = FAILED
        elif self._internal_state == _CANCELLING_AFTER_STARTED:
            self._internal_state = CANCELLED
        else:
            raise _StateTransitionError(
                "Unexpected 'raised' message in internal state {!r}".format(
                    self._internal_state
                )
            )

    def _user_cancelled(self):
        """
        Update state when the user requests cancellation.

        A future in ``WAITING`` or ``EXECUTING`` state moves to ``CANCELLING``
        state.
        """
        if self._internal_state == _INITIALIZED:
            self._cancel()
            self._internal_state = _CANCELLING_BEFORE_STARTED
        elif self._internal_state == EXECUTING:
            self._cancel()
            self._internal_state = _CANCELLING_AFTER_STARTED
        else:
            raise _StateTransitionError(
                "Unexpected 'cancelled' message in internal state {!r}".format(
                    self._internal_state
                )
            )

    def _executor_initialized(self, cancel):
        """
        Update state when the executor initializes the future.

        Parameters
        ----------
        cancel : callable
            The callback to be called when the user requests cancellation.
            The callback accepts no arguments, and has no return value.
        """
        if self._internal_state == _NOT_INITIALIZED:
            self._cancel = cancel
            self._internal_state = _INITIALIZED
        else:
            raise _StateTransitionError(
                "Unexpected initialization in internal state {!r}".format(
                    self._internal_state
                )
            )

    # Private traits ##########################################################

    #: Callback called (with no arguments) when user requests cancellation.
    #: This is reset to ``None`` once cancellation is impossible.
    _cancel = Callable(allow_none=True)

    #: The internal state of the future.
    _internal_state = Enum(_NOT_INITIALIZED, list(_INTERNAL_STATE_TO_STATE))

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    def _get_state(self):
        """ Property getter for the "state" trait. """
        return _INTERNAL_STATE_TO_STATE[self._internal_state]

    def _get_cancellable(self):
        """ Property getter for the "cancellable" trait. """
        return self._internal_state in _CANCELLABLE_INTERNAL_STATES

    def _get_done(self):
        """ Property getter for the "done" trait. """
        return self._internal_state in _DONE_INTERNAL_STATES

    def __internal_state_changed(self, old_internal_state, new_internal_state):
        """ Trait change handler for the "_internal_state" trait. """
        old_state = _INTERNAL_STATE_TO_STATE[old_internal_state]
        new_state = _INTERNAL_STATE_TO_STATE[new_internal_state]
        if old_state != new_state:
            self.trait_property_changed("state", old_state, new_state)

        old_cancellable = old_internal_state in _CANCELLABLE_INTERNAL_STATES
        new_cancellable = new_internal_state in _CANCELLABLE_INTERNAL_STATES
        if old_cancellable != new_cancellable:
            self.trait_property_changed(
                "cancellable", old_cancellable, new_cancellable
            )

        old_done = old_internal_state in _DONE_INTERNAL_STATES
        new_done = new_internal_state in _DONE_INTERNAL_STATES
        if old_done != new_done:
            self.trait_property_changed("done", old_done, new_done)
