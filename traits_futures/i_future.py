# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Interface for futures returned by the executor.
"""

import abc

from traits.api import Bool, Interface, Property

from traits_futures.future_states import FutureState


class IFuture(Interface):
    """
    Interface for futures returned by the executor.
    """

    #: The known state of the background task. One of the six constants
    #: ``WAITING``, ``EXECUTING``, ``COMPLETED``, ``FAILED``, ``CANCELLING``
    #: or ``CANCELLED``.
    state = FutureState

    #: True if this task can be cancelled, else False. A task can be
    #: cancelled only if ``state`` is ``WAITING`` or ``EXECUTING``. The
    #: observed value of this trait will always be consistent with ``state``.
    cancellable = Property(Bool())

    #: True if the task has finished and no further state changes will occur.
    #: The value of ``done`` is ``True`` if and only if the ``state`` attribute
    #: is one of ``COMPLETED``, ``FAILED``, or ``CANCELLED``. It's safe to
    #: listen to this trait for changes: it will always fire exactly once.
    done = Property(Bool())

    @abc.abstractmethod
    def cancel(self):
        """
        Request cancellation of the background task.

        A task in WAITING or EXECUTING state will immediately be moved to
        CANCELLING state. If the task is not in WAITING or EXECUTING state,
        this function will raise ``RuntimeError``.

        Raises
        ------
        RuntimeError
            If the task has already completed, or cancellation has already
            been requested.
        """

    @property
    @abc.abstractmethod
    def result(self):
        """
        Result of the background task.

        This attribute is only available if the state of the future is
        COMPLETED. If the future has not reached the COMPLETED state, any
        attempt to access this attribute will give AttributeError.
        """

    @property
    @abc.abstractmethod
    def exception(self):
        """
        Exception raised by the background task.

        This attribute is only available if the state of the future is
        FAILED. If the future has not reached the FAILED state, any
        attempt to access this attribute will give AttributeError.
        """
