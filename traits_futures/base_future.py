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
Base class providing common pieces of the Future machinery.
"""

import abc
import logging

from traits.api import (
    Any,
    Bool,
    Callable,
    Enum,
    HasRequiredTraits,
    observe,
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
from traits_futures.i_task_specification import IFuture

logger = logging.getLogger(__name__)

# Messages sent by the BaseTask, and interpreted by BaseFuture.

#: Custom message from the future. The argument is a pair
#: (message_type, message_args); the message type and message args
#: are interpreted by the future.
SENT = "sent"

#: Control message sent when the callable is abandoned before execution.
ABANDONED = "abandoned"

#: Control message sent before we start to process the target callable.
#: The argument is always ``None``.
STARTED = "started"

#: Control message sent when an exception was raised by the background
#: callable. The argument is a tuple containing exception information.
RAISED = "raised"

#: Control message sent to indicate that the background callable succeeded
#: and returned a result. The argument is that result.
RETURNED = "returned"

#: Message types that indicate a "final" message. After a message of this
#: type is received, no more messages will be received.
FINAL_MESSAGES = {ABANDONED, RAISED, RETURNED}

# The BaseFuture class maintains an internal state. That internal state maps to
# the user-facing state, but is more fine-grained, allowing the class to keep
# track of the internal consistency and invariants. For example, the
# user-facing CANCELLING state doesn't indicate whether the task has started
# or not; if it *has* already started, then a "start" message from the
# background task is invalid; otherwise, it's valid. So we split this into
# two internal states: _CANCELLING_BEFORE_STARTED and _CANCELLING_AFTER_STARTED
# to allow us to detect an invalid _task_started call.


#: Internal state attained when cancellation is requested before the task
#: starts.
_CANCELLING_BEFORE_STARTED = "cancelling_before_started"

#: Internal state attained when cancellation is requested after the task
#: starts.
_CANCELLING_AFTER_STARTED = "cancelling_after_started"

#: Internal state corresponding to a task that was abandoned due to
#: cancellation.
_CANCELLED_ABANDONED = "cancelled_abandoned"

#: Internal state corresponding to a task that failed after cancellation.
_CANCELLED_FAILED = "cancelled_failed"

#: Internal state corresponding to a task that completed after cancellation.
_CANCELLED_COMPLETED = "cancelled_completed"

#: Mapping from each internal state to the corresponding user-visible state.
_INTERNAL_STATE_TO_STATE = {
    WAITING: WAITING,
    EXECUTING: EXECUTING,
    COMPLETED: COMPLETED,
    FAILED: FAILED,
    _CANCELLING_BEFORE_STARTED: CANCELLING,
    _CANCELLING_AFTER_STARTED: CANCELLING,
    _CANCELLED_ABANDONED: CANCELLED,
    _CANCELLED_COMPLETED: CANCELLED,
    _CANCELLED_FAILED: CANCELLED,
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


class TaskCancelled(Exception):
    """
    Exception raised within the background task on cancellation.
    """


class _StateTransitionError(Exception):
    """
    Exception used to indicate a bad state transition.

    Users should never see this exception. It indicates an error in the
    sequence of operations received by the future from the background
    task, from the executor, or from the user.
    """


@IFuture.register
class BaseFuture(HasRequiredTraits):
    """
    Convenience base class for the various flavours of Future.
    """

    # IFuture interface #######################################################

    def cancel(self):
        """
        Request cancellation of the background task.

        A task in ``WAITING`` or ``EXECUTING`` state will immediately be moved
        to ``CANCELLING`` state. If the task is not in ``WAITING`` or
        ``EXECUTING`` state, this function does nothing.

        .. versionchanged:: 0.3.0

           This method no longer raises for a task that isn't cancellable.
           In previous versions, :exc:`RuntimeError` was raised.

        Returns
        -------
        cancelled : bool
            True if the task was cancelled, False if the task was not
            cancellable.
        """
        if self.state in {WAITING, EXECUTING}:
            self._user_cancelled()
            logger.debug(f"{self} cancelled")
            return True
        else:
            logger.debug(f"{self} not cancellable; state is {self.state}")
            return False

    def receive(self, message):
        """
        Receive and process a message from the task associated to this future.

        This method is primarily for use by the executors, but may also be of
        use in testing.

        Parameters
        ----------
        message : object
            The message received from the associated task.

        Returns
        -------
        final : bool
            True if the received message should be the last one ever received
            from the paired task.
        """
        message_type, message_arg = message
        method_name = "_task_{}".format(message_type)
        getattr(self, method_name)(message_arg)
        return message_type in FINAL_MESSAGES

    # BaseFuture interface ####################################################

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
        exc_info : tuple
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

    def dispatch(self, message):
        """
        Dispatch a message arriving from the associated BaseTask.

        This is a convenience function, and may be safely overridden by
        subclasses that want to use a different dispatch mechanism. For
        a message type ``msgtype``, it looks for a method called
        ``_process_<msgtype>`` and dispatches the message arguments to
        that method. Subclasses then only need to provide the appropriate
        ``_process_<msgtype>`` methods.

        Parameters
        ----------
        message : object
            Message sent by the background task. The default implementation of
            this method expects the message to be in the form ``(message_type,
            message_args)`` with ``message_type`` a string.
        """
        message_type, message_arg = message
        method_name = "_process_{}".format(message_type)
        getattr(self, method_name)(message_arg)

    # State transitions #######################################################

    # These methods represent state transitions in response to external events.

    def _task_sent(self, message):
        """
        Automate dispatch of different types of message.

        Delegates the actual work to the :meth:`dispatch` method,
        which can be overridden by subclasses. Messages received after
        cancellation are ignored.

        Parameters
        ----------
        message : object
            Message from the background task.
        """

        if self._internal_state == _CANCELLING_AFTER_STARTED:
            # Ignore messages that arrive after a cancellation request.
            return
        elif self._internal_state == EXECUTING:
            self.dispatch(message)
        else:
            raise _StateTransitionError(
                "Unexpected custom message in internal state {!r}".format(
                    self._internal_state
                )
            )

    def _task_abandoned(self, none):
        """
        Update state when the background task is abandoned due to cancellation.

        Internal state:
        * _CANCELLING_BEFORE_STARTED -> _CANCELLED_ABANDONED

        Parameters
        ----------
        none : NoneType
            This parameter is unused.
        """
        if self._internal_state == _CANCELLING_BEFORE_STARTED:
            self._cancel = None
            self._internal_state = _CANCELLED_ABANDONED
        else:
            raise _StateTransitionError(
                "Unexpected 'started' message in internal state {!r}".format(
                    self._internal_state
                )
            )

    def _task_started(self, none):
        """
        Update state when the background task has started processing.

        Internal state:
        * WAITING -> EXECUTING
        * _CANCELLING_BEFORE_STARTED -> _CANCELLED_AFTER_STARTED

        Parameters
        ----------
        none : NoneType
            This parameter is unused.
        """
        if self._internal_state == WAITING:
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

        Internal state:
        * EXECUTING -> COMPLETED
        * _CANCELLING_AFTER_STARTED -> _CANCELLED_COMPLETED

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
            self._cancel = None
            self._result = result
            self._internal_state = _CANCELLED_COMPLETED
        else:
            raise _StateTransitionError(
                "Unexpected 'returned' message in internal state {!r}".format(
                    self._internal_state
                )
            )

    def _task_raised(self, exception_info):
        """
        Update state when the background task reports completing with an error.

        Internal state:
        * EXECUTING -> FAILED
        * _CANCELLING_AFTER_STARTED -> _CANCELLED_FAILED

        Parameters
        ----------
        exception_info : tuple
            Tuple containing exception information in string form:
            (exception type, exception value, formatted traceback).
        """
        if self._internal_state == EXECUTING:
            self._cancel = None
            self._exception = exception_info
            self._internal_state = FAILED
        elif self._internal_state == _CANCELLING_AFTER_STARTED:
            self._cancel = None
            self._exception = exception_info
            self._internal_state = _CANCELLED_FAILED
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

        Internal state:
        * WAITING -> _CANCELLING_BEFORE_STARTED
        * EXECUTING -> _CANCELLING_AFTER_STARTED
        """
        if self._internal_state == WAITING:
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

    # Private traits ##########################################################

    #: Callback called (with no arguments) when user requests cancellation.
    #: This is reset to ``None`` once cancellation is impossible.
    _cancel = Callable(allow_none=True, required=True)

    #: The internal state of the future.
    _internal_state = Enum(WAITING, list(_INTERNAL_STATE_TO_STATE))

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    def _get_state(self):
        """Property getter for the "state" trait."""
        return _INTERNAL_STATE_TO_STATE[self._internal_state]

    def _get_cancellable(self):
        """Property getter for the "cancellable" trait."""
        return self._internal_state in _CANCELLABLE_INTERNAL_STATES

    def _get_done(self):
        """Property getter for the "done" trait."""
        return self._internal_state in _DONE_INTERNAL_STATES

    @observe("_internal_state")
    def _update_property_traits(self, event):
        """Trait change handler for the "_internal_state" trait."""
        old_internal_state, new_internal_state = event.old, event.new

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


class BaseTask(abc.ABC):
    """
    Mixin for background task classes, making those classes callable.

    This class provides a callable wrapper allowing subclasses to easily
    provide a background callable task.

    Subclasses should override the ``run`` method to customize what should
    happen when the task runs. This class's ``__call__`` implementation will
    take care of sending standard control messages telling the future that the
    task has started, completed, or raised, and delegate to the ``run`` method
    for execution of the background task and sending of any custom messages.
    """

    @abc.abstractmethod
    def run(self):
        """
        Run the body of the background task.

        Returns
        -------
        any : object
            May return any object. That object will be delivered to the
            future's ``result`` attribute.
        """

    def send(self, message_type, message_arg=None):
        """
        Send a message to the associated future.

        Parameters
        ----------
        message_type : str
            The type of the message. This is used by ``BaseFuture`` when
            dispatching messages to appropriate handlers.
        message_arg : object, optional
            Message argument, if any. If not given, ``None`` is used.
        """
        self.__send((SENT, (message_type, message_arg)))

    def cancelled(self):
        """
        Determine whether the user has requested cancellation.

        Returns True if the user has requested cancellation via the associated
        future's ``cancel`` method, and False otherwise.

        Returns
        -------
        bool
        """
        return self.__cancelled()

    def __call__(self, send, cancelled):
        self.__send = send
        self.__cancelled = cancelled
        try:
            if cancelled():
                send((ABANDONED, None))
                return

            send((STARTED, None))
            try:
                result = self.run()
            except BaseException as e:
                send((RAISED, marshal_exception(e)))
            else:
                send((RETURNED, result))
        finally:
            del self.__cancelled
            del self.__send
