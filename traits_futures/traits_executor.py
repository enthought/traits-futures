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
Executor to submit background tasks.
"""

import concurrent.futures
import logging
import threading
import warnings

from traits.api import (
    Any,
    Bool,
    Enum,
    HasStrictTraits,
    Instance,
    on_trait_change,
    Property,
    Set,
)

from traits_futures.background_call import submit_call
from traits_futures.background_iteration import submit_iteration
from traits_futures.background_progress import submit_progress
from traits_futures.ets_context import ETSContext
from traits_futures.executor_states import (
    ExecutorState,
    RUNNING,
    STOPPED,
    STOPPING,
)
from traits_futures.i_gui_context import IGuiContext
from traits_futures.i_parallel_context import IParallelContext
from traits_futures.multithreading_context import MultithreadingContext
from traits_futures.wrappers import BackgroundTaskWrapper, FutureWrapper

logger = logging.getLogger(__name__)


# The TraitsExecutor class maintains an internal state that maps to the
# publicly visible state. The internal state keeps track of some extra
# details about the shutdown.

#: Mapping from each internal state to the corresponding user-visible state.
_INTERNAL_STATE_TO_EXECUTOR_STATE = {
    RUNNING: RUNNING,
    STOPPING: STOPPING,
    STOPPED: STOPPED,
}

#: Set of internal states that are considered to be "running" states.
_RUNNING_INTERNAL_STATES = {
    internal_state
    for internal_state, state in _INTERNAL_STATE_TO_EXECUTOR_STATE.items()
    if state == RUNNING
}

#: Set of internal states that are considered to be "stopped" states.
_STOPPED_INTERNAL_STATES = {
    internal_state
    for internal_state, state in _INTERNAL_STATE_TO_EXECUTOR_STATE.items()
    if state == STOPPED
}


class _StateTransitionError(Exception):
    """
    Exception used to indicate a bad state transition.

    Users should never see this exception. It always indicates an error in the
    executor logic.
    """


class TraitsExecutor(HasStrictTraits):
    """
    Executor to initiate and manage background tasks.

    Parameters
    ----------
    thread_pool : concurrent.futures.Executor, optional
        Deprecated alias for worker_pool.

        .. deprecated:: 0.2
           Use ``worker_pool`` instead.

    worker_pool : concurrent.futures.Executor, optional
        If supplied, provides the underlying worker pool executor to use. In
        this case, the creator of the TraitsExecutor is responsible for
        shutting down the worker pool once it's no longer needed. If not
        supplied, a new private worker pool will be created, and this object's
        ``stop`` method will shut down that worker pool.
    max_workers : int or None, optional
        Maximum number of workers for the private worker pool. This parameter
        is mutually exclusive with ``worker_pool``. The default is ``None``,
        which delegates the choice of number of workers to Python's
        ``concurrent.futures`` module.
    context : IParallelContext, optional
        Parallelism context, providing appropriate concurrent primitives
        and worker pools for a given choice of parallelism (for example
        multithreading or multiprocessing). If not given, assumes
        multithreading. Note that if both ``context`` and ``worker_pool``
        are given, they must be compatible.
    gui_context : IGuiContext, optional
        Context providing information about which GUI event loop to use. If not
        given, uses an :class:`~.ETSContext` instance, which determines the
        appropriate toolkit based on availability.
    """

    #: Current state of this executor.
    state = Property(ExecutorState)

    #: Derived state: true if this executor is running; False if it's
    #: stopped or stopping.
    running = Property(Bool())

    #: Derived state: true if this executor is stopped and it's safe
    #: to dispose of related resources (like the worker pool).
    stopped = Property(Bool())

    def __init__(
        self,
        thread_pool=None,
        *,
        worker_pool=None,
        max_workers=None,
        context=None,
        gui_context=None,
        **traits,
    ):
        super().__init__(**traits)

        if thread_pool is not None:
            warnings.warn(
                (
                    "The thread_pool argument to TraitsExecutor is "
                    "deprecated. Use worker_pool instead."
                ),
                category=DeprecationWarning,
                stacklevel=2,
            )
            worker_pool = thread_pool

        if context is not None:
            self._context = context

        if gui_context is not None:
            self._gui_context = gui_context

        own_worker_pool = worker_pool is None
        if own_worker_pool:
            logger.debug(f"{self} creating worker pool")
            if max_workers is None:
                worker_pool = self._context.worker_pool()
            else:
                worker_pool = self._context.worker_pool(
                    max_workers=max_workers
                )
        elif max_workers is not None:
            raise TypeError(
                "at most one of 'worker_pool' and 'max_workers' "
                "should be supplied"
            )

        self._worker_pool = worker_pool
        self._own_worker_pool = own_worker_pool

        logger.debug(f"{self} running")

    def submit_call(self, callable, *args, **kwargs):
        """
        Convenience function to submit a background call.

        .. deprecated:: 0.2
           Use the :func:`~.submit_call` function instead.

        Parameters
        ----------
        callable : an arbitrary callable
            Function to execute in the background.
        *args
            Positional arguments to pass to that function.
        **kwargs
            Named arguments to pass to that function.

        Returns
        -------
        future : CallFuture
            Object representing the state of the background call.
        """
        warnings.warn(
            "The submit_call method is deprecated. Use the submit_call "
            "convenience function instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return submit_call(self, callable, *args, **kwargs)

    def submit_iteration(self, callable, *args, **kwargs):
        """
        Convenience function to submit a background iteration.

        .. deprecated:: 0.2
           Use the :func:`~.submit_iteration` function instead.

        Parameters
        ----------
        callable : an arbitrary callable
            Function executed in the background to provide the iterable.
        *args
            Positional arguments to pass to that function.
        **kwargs
            Named arguments to pass to that function.

        Returns
        -------
        future : IterationFuture
            Object representing the state of the background iteration.
        """
        warnings.warn(
            "The submit_iteration method is deprecated. Use the "
            "submit_iteration convenience function instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return submit_iteration(self, callable, *args, **kwargs)

    def submit_progress(self, callable, *args, **kwargs):
        """
        Convenience function to submit a background progress call.

        .. deprecated:: 0.2
           Use the :func:`~.submit_progress` function instead.

        Parameters
        ----------
        callable : callable accepting a "progress" named argument
            Function executed in the background to provide the iterable. This
            should accept a "progress" named argument. The callable can then
            call the "progress" object to report progress.
        *args
            Positional arguments to pass to that function.
        **kwargs
            Named arguments to pass to that function. These should not include
            "progress".

        Returns
        -------
        future : ProgressFuture
            Object representing the state of the background task.
        """
        warnings.warn(
            "The submit_progress method is deprecated. Use the "
            "submit_progress convenience function instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return submit_progress(self, callable, *args, **kwargs)

    def submit(self, task):
        """
        Submit a task to the executor, and return the corresponding future.

        This method is not thread-safe. It may only be used from the main
        thread.

        Parameters
        ----------
        task : ITaskSpecification

        Returns
        -------
        future : IFuture
            Future for this task.
        """
        # We may relax this one day, but for now tasks may only be submitted
        # from the main thread. ref: enthought/traits-futures#302.
        if threading.current_thread() != threading.main_thread():
            raise RuntimeError(
                "Tasks may only be sumitted on the main thread."
            )

        if not self.running:
            raise RuntimeError("Can't submit task unless executor is running.")

        cancel_event = self._context.event()

        sender, receiver = self._message_router.pipe()
        try:
            runner = task.background_task()
            future = task.future()
            future._executor_initialized(cancel_event.set)
        except Exception:
            self._message_router.close_pipe(receiver)
            raise

        background_task_wrapper = BackgroundTaskWrapper(
            runner, sender, cancel_event
        )
        self._worker_pool.submit(background_task_wrapper)

        future_wrapper = FutureWrapper(
            future=future,
            receiver=receiver,
        )
        self._wrappers.add(future_wrapper)

        logger.debug(f"{self} created future {future}")
        return future

    def stop(self):
        """
        Initiate stop: cancel existing jobs and prevent new ones.
        """
        if not self.running:
            raise RuntimeError("Executor is not currently running.")

        self._initiate_stop()
        if not self._wrappers:
            self._complete_stop()

    # State transitions #######################################################

    def _stop_router(self):
        """
        Stop the message router.
        """
        if self._have_message_router:
            logger.debug(f"{self} stopping message router")
            for wrapper in self._wrappers:
                self._message_router.close_pipe(wrapper.receiver)
            self._message_router.stop()
            self._message_router = None
            self._have_message_router = False
            logger.debug(f"{self} message router stopped")

    def _close_context(self):
        """
        Close the context, if we own it.
        """
        if self._own_context:
            logger.debug(f"{self} closing context")
            self._context.close()
            logger.debug(f"{self} context closed")
        self._context = None

    def _shutdown_worker_pool(self):
        """
        Shut down the worker pool if we own it.
        """
        if self._own_worker_pool:
            logger.debug(f"{self} shutting down owned worker pool")
            # The worker pool shutdown call is potentially blocking, but we
            # should only ever reach this line when all the background tasks
            # are complete, so in practice it should never block for long.
            self._worker_pool.shutdown()
            logger.debug(f"{self} worker pool is now shut down")
        self._worker_pool = None

    def _cancel_tasks(self):
        """
        Cancel all currently running tasks.
        """
        logger.debug("Cancelling incomplete tasks")
        cancel_count = 0
        for wrapper in self._wrappers:
            future = wrapper.future
            if future.cancellable:
                future.cancel()
                cancel_count += 1
        logger.debug(f"{cancel_count} tasks cancelled")

    def _initiate_stop(self):
        """
        Prevent new tasks from being submitted and cancel existing tasks.

        State: RUNNING -> STOPPING
        """
        if self._internal_state == RUNNING:
            self._cancel_tasks()
            self._internal_state = STOPPING
        else:
            raise _StateTransitionError(
                "Unexpected state transition in internal state {!r}".format(
                    self._internal_state
                )
            )

    def _complete_stop(self):
        """
        Move to stopped state when all remaining futures have completed.

        State: STOPPING -> STOPPED
        """
        if self._internal_state == STOPPING:
            self._stop_router()
            self._close_context()
            self._shutdown_worker_pool()
            self._internal_state = STOPPED
        else:
            raise _StateTransitionError(
                "Unexpected state transition in internal state {!r}".format(
                    self._internal_state
                )
            )

    # Private traits ##########################################################

    #: Internal state of the executor.
    _internal_state = Enum(RUNNING, list(_INTERNAL_STATE_TO_EXECUTOR_STATE))

    #: Wrappers for currently-executing futures.
    _wrappers = Set(Instance(FutureWrapper))

    #: Parallelization context
    _context = Instance(IParallelContext)

    #: GUI toolkit context
    _gui_context = Instance(IGuiContext)

    #: True if we own this context, else False.
    _own_context = Bool(False)

    #: concurrent.futures.Executor instance providing the worker pool.
    _worker_pool = Instance(concurrent.futures.Executor)

    #: True if we own this worker pool (and are therefore responsible
    #: for shutting it down), else False.
    _own_worker_pool = Bool()

    #: Router providing message connections between background tasks
    #: and foreground futures.
    _message_router = Any()

    #: True if we've created a message router, and need to shut it down.
    _have_message_router = Bool(False)

    # Private methods #########################################################

    def _get_state(self):
        """Property getter for the "state" trait."""
        return _INTERNAL_STATE_TO_EXECUTOR_STATE[self._internal_state]

    def _get_running(self):
        """Property getter for the "running" trait."""
        return self._internal_state in _RUNNING_INTERNAL_STATES

    def _get_stopped(self):
        """Property getter for the "stopped" trait."""
        return self._internal_state in _STOPPED_INTERNAL_STATES

    def __internal_state_changed(self, old_internal_state, new_internal_state):
        """Trait change handler for the "_internal_state" trait."""
        logger.debug(
            "Executor internal state changed "
            f"from {old_internal_state} to {new_internal_state}"
        )

        old_state = _INTERNAL_STATE_TO_EXECUTOR_STATE[old_internal_state]
        new_state = _INTERNAL_STATE_TO_EXECUTOR_STATE[new_internal_state]
        if old_state != new_state:
            self.trait_property_changed("state", old_state, new_state)

        old_running = old_internal_state in _RUNNING_INTERNAL_STATES
        new_running = new_internal_state in _RUNNING_INTERNAL_STATES
        if old_running != new_running:
            self.trait_property_changed("running", old_running, new_running)

        old_stopped = old_internal_state in _STOPPED_INTERNAL_STATES
        new_stopped = new_internal_state in _STOPPED_INTERNAL_STATES
        if old_stopped != new_stopped:
            self.trait_property_changed("stopped", old_stopped, new_stopped)

    def __message_router_default(self):
        # Toolkit-specific message router.
        router = self._context.message_router(gui_context=self._gui_context)
        router.start()
        self._have_message_router = True
        return router

    def __gui_context_default(self):
        # By default we use the "ETS" GUI context, which chooses which
        # GUI toolkit to use based on the ETS_TOOLKIT environment variable
        # and the available installed packages.
        return ETSContext()

    def __context_default(self):
        # By default, we use multithreading.
        context = MultithreadingContext()
        self._own_context = True
        return context

    @on_trait_change("_wrappers:done")
    def _untrack_future(self, wrapper, name, is_done):
        self._message_router.close_pipe(wrapper.receiver)
        self._wrappers.remove(wrapper)
        logger.debug(
            f"{self} future {wrapper.future} done ({wrapper.future.state})"
        )
        # If we're in STOPPING state and the last future has just exited,
        # go to STOPPED state.
        if self._internal_state == STOPPING and not self._wrappers:
            self._complete_stop()
