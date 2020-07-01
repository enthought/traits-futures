# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Interface for futures returned by the executor.
"""

import abc

from traits.api import ABCHasStrictTraits, Bool, Property

from traits_futures.future_states import FutureState


class IFuture(ABCHasStrictTraits):
    """
    Interface for futures returned by the executor.
    """

    #: The known state of the background task. One of the constants
    #: ``EXECUTING``, ``CANCELLING``, ``CANCELLED``, or ``COMPLETED``.
    state = FutureState

    #: True if this task can be cancelled, else False. A task can be
    #: cancelled only if ``state`` is ``EXECUTING``. The observed value
    #: of this trait should always be consistent with ``state``.
    cancellable = Property(Bool())

    #: True if the task state is either ``CANCELLED`` or ``COMPLETED``.
    #: The observed value of this trait should always be consistent
    #: with ``state``. It's safe to listen to this trait for changes: it
    #: will always fire exactly once.
    done = Property(Bool())

    @abc.abstractmethod
    def cancel(self):
        """
        Request cancellation of the background task.

        A task in EXECUTING state will immediately be moved to CANCELLING
        state. If the task is not in EXECUTING state, this function will
        raise ``RuntimeError``.

        Raises
        ------
        RuntimeError
            If the task has already completed, or cancellation has already
            been requested.
        """
