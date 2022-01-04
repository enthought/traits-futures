# (C) Copyright 2018-2022 Enthought, Inc., Austin, TX
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
    observe,
    Property,
    Set,
)

from traits_futures.background_call import submit_call
from traits_futures.background_iteration import submit_iteration
from traits_futures.background_progress import submit_progress
from traits_futures.ets_event_loop import ETSEventLoop
from traits_futures.executor_states import (
    ExecutorState,
    RUNNING,
    STOPPED,
    STOPPING,
)
from traits_futures.i_event_loop import IEventLoop
from traits_futures.i_parallel_context import IParallelContext
from traits_futures.multithreading_context import MultithreadingContext
from traits_futures.wrappers import FutureWrapper, run_background_task

logger = logging.getLogger(__name__)


# The TraitsExecutor class maintains an internal state that maps to the
# publicly visible state. The internal state keeps track of some extra
# details about the shutdown.

#: Internal state arising from a timeout on "shutdown": all tasks have been
#: cancelled and the background tasks have been unlinked from their
#: corresponding futures, but some background tasks may still be executing.
#: Maps to the STOPPING public state.
_TERMINATING = "terminating"

#: Mapping from each internal state to the corresponding user-visible state.
_INTERNAL_STATE_TO_EXECUTOR_STATE = {
    RUNNING: RUNNING,
    STOPPING: STOPPING,
    STOPPED: STOPPED,
    _TERMINATING: STOPPING,
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
    event_loop : IEventLoop, optional
        The event loop to use for message dispatch. If not given, uses an
        :class:`~.ETSEventLoop` instance, which determines the appropriate
        toolkit based on availability and the value of the ETS_TOOLKIT
        environment variable.
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
        event_loop=None,
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

        if event_loop is not None:
            self._event_loop = event_loop

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
        callable
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
        callable
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
        callable
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
        runner = task.task()
        future = task.future(cancel_event.set)

        self._worker_pool.submit(
            run_background_task, runner, sender, cancel_event.is_set
        )

        future_wrapper = FutureWrapper(
            future=future,
            receiver=receiver,
        )
        self._wrappers.add(future_wrapper)

        logger.debug(f"{self} created future {future}")
        return future

    def shutdown(self, *, timeout=None):
        """
        Wait for all tasks to complete and then shut this executor down.

        All waiting or executing background tasks that are cancellable will be
        cancelled, and then this executor will wait for all tasks to complete.
        If a timeout is given and that timeout is reached before all tasks
        complete, then :exc:`RuntimeError` will be raised and the executor will
        remain in :data:`~.STOPPING` state. Otherwise, on return from this
        method the executor will be in :data:`~.STOPPED` state

        This method may be called at any time. If called on an executor
        that's already stopped, this method does nothing.

        Parameters
        ----------
        timeout : float, optional
            Maximum time to wait for background tasks to complete, in seconds.
            If not given, this method will wait indefinitely.

        Raises
        ------
        RuntimeError
            If a timeout is given, and the background tasks fail to complete
            within the given timeout.
        """
        if self.stopped:
            return

        if self._internal_state == RUNNING:
            self._initiate_stop()
        if self._internal_state == STOPPING:
            self._initiate_manual_stop()

        assert self._internal_state == _TERMINATING

        if self._have_message_router:
            try:
                self._message_router.route_until(
                    lambda: not self._wrappers,
                    timeout=timeout,
                )
            except RuntimeError as exc:
                # Re-raise with a more user-friendly error message.
                raise RuntimeError(
                    "Shutdown timed out; "
                    f"{len(self._wrappers)} tasks still running"
                ) from exc

        self._complete_stop()

    def stop(self):
        """
        Initiate stop: cancel existing jobs and prevent new ones.
        """
        if not self.running:
            raise RuntimeError("Executor is not currently running.")

        self._initiate_stop()

        # If there are no tasks pending we can complete the stop immediately;
        # otherwise, we check as each task completes using the observer below.
        if not self._wrappers:
            self._complete_stop()

    @observe("_wrappers:items:done")
    def _finalize_task_and_check_for_stop(self, event):
        wrapper = event.object
        self._message_router.close_pipe(wrapper.receiver)
        self._wrappers.remove(wrapper)
        logger.debug(
            f"{self} future {wrapper.future} done ({wrapper.future.state})"
        )
        # If we're in STOPPING state and the last future has just exited,
        # clean up and stop.
        if self._internal_state == STOPPING:
            if not self._wrappers:
                self._complete_stop()

    # State transitions #######################################################

    def _initiate_stop(self):
        """
        Prevent new tasks from being submitted and cancel existing tasks.

        Internal state: RUNNING -> STOPPING
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

        Internal state:

        * STOPPING -> STOPPED
        * _TERMINATING -> STOPPED
        """
        if self._internal_state in {STOPPING, _TERMINATING}:
            # We should only get here once all futures have completed.
            assert not self._wrappers

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

    def _initiate_manual_stop(self):
        """
        Move into manual stopping mode (_TERMINATING internal state).

        This differs from the STOPPING internal state in its handling of
        completed futures: an executor in STOPPING state moves to STOPPED state
        automatically when the last task completes. An executor in _TERMINATING
        state must complete the stop manually.

        Internal state: STOPPING -> _TERMINATING
        """
        if self._internal_state == STOPPING:
            self._internal_state = _TERMINATING
        else:
            raise _StateTransitionError(
                "Unexpected state transition in internal state {!r}".format(
                    self._internal_state
                )
            )

    # Private methods #########################################################

    def _cancel_tasks(self):
        """
        Cancel all currently running tasks.
        """
        logger.debug(f"{self} cancelling incomplete tasks")
        cancel_count = 0
        for wrapper in self._wrappers:
            cancel_count += wrapper.future.cancel()
        logger.debug(f"{self} cancelled {cancel_count} tasks")

    def _stop_router(self):
        """
        Stop the message router.
        """
        if self._have_message_router:
            logger.debug(f"{self} stopping message router")
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
        Shut down the worker pool, if we own it.
        """
        if self._own_worker_pool:
            logger.debug(f"{self} shutting down owned worker pool")
            # The worker pool shutdown call is potentially blocking, but we
            # should only ever reach this line when all the background tasks
            # are complete, so in practice it should never block for long.
            self._worker_pool.shutdown()
            logger.debug(f"{self} worker pool is now shut down")
        self._worker_pool = None

    # Private traits ##########################################################

    #: Internal state of the executor.
    _internal_state = Enum(RUNNING, list(_INTERNAL_STATE_TO_EXECUTOR_STATE))

    #: Wrappers for currently-executing futures.
    _wrappers = Set(Instance(FutureWrapper))

    #: Parallelization context
    _context = Instance(IParallelContext)

    #: Event loop used for message dispatch
    _event_loop = Instance(IEventLoop)

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

    @observe("_internal_state")
    def _update_property_traits(self, event):
        """Trait change handler for the "_internal_state" trait."""
        old_internal_state, new_internal_state = event.old, event.new

        logger.debug(
            f"{self} internal state changed "
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
        router = self._context.message_router(event_loop=self._event_loop)
        router.start()
        self._have_message_router = True
        return router

    def __event_loop_default(self):
        # By default we use the "ETS" event loop, which chooses which
        # event loop to use based on the ETS_TOOLKIT environment variable
        # and the available installed packages.
        return ETSEventLoop()

    def __context_default(self):
        # By default, we use multithreading.
        context = MultithreadingContext()
        self._own_context = True
        return context
