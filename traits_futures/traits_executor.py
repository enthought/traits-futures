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
Executor to submit background tasks.
"""

import concurrent.futures
import warnings

from traits.api import (
    Any,
    Bool,
    Dict,
    Enum,
    HasStrictTraits,
    Instance,
    on_trait_change,
    Property,
)

from traits_futures.background_call import submit_call
from traits_futures.background_iteration import submit_iteration
from traits_futures.background_progress import submit_progress
from traits_futures.i_parallel_context import IParallelContext
from traits_futures.wrappers import BackgroundTaskWrapper, FutureWrapper


# Executor states.

#: Executor is currently running (this is the initial state).
RUNNING = "running"

#: Executor has been requested to stop. In this state, no new
#: jobs can be submitted, and we're waiting for old ones to complete.
STOPPING = "stopping"

#: Executor is stopped.
STOPPED = "stopped"

#: Trait type representing the executor state.
ExecutorState = Enum(RUNNING, STOPPING, STOPPED)


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
    """

    #: Current state of this executor.
    state = ExecutorState

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
        **traits,
    ):
        super(TraitsExecutor, self).__init__(**traits)

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

        own_worker_pool = worker_pool is None
        if own_worker_pool:
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

        Parameters
        ----------
        task : ITaskSpecification

        Returns
        -------
        future : IFuture
            Future for this task.
        """
        if not self.running:
            raise RuntimeError("Can't submit task unless executor is running.")

        cancel_event = self._context.event()

        sender, receiver = self._message_router.pipe()
        try:
            runner = task.background_task()
            future = task.future()
            future._executor_initialized(cancel_event.set)
        except Exception:
            self._message_router.close_pipe(sender, receiver)
            raise

        background_task_wrapper = BackgroundTaskWrapper(
            runner, sender, cancel_event
        )
        wrapper = FutureWrapper(future=future, receiver=receiver)
        self._worker_pool.submit(background_task_wrapper)
        self._wrappers[receiver] = wrapper
        return future

    def stop(self):
        """
        Initiate stop: cancel existing jobs and prevent new ones.
        """
        if not self.running:
            raise RuntimeError("Executor is not currently running.")

        # For consistency, we always go through the STOPPING state,
        # even if there are no jobs.
        self.state = STOPPING

        # Cancel any futures that aren't already cancelled.
        for _, wrapper in self._wrappers.items():
            future = wrapper.future
            if future.cancellable:
                future.cancel()

        if not self._wrappers:
            self._stop()

    # Private traits ##########################################################

    #: Parallelization context
    _context = Instance(IParallelContext)

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

    #: Wrappers for currently-executing futures.
    _wrappers = Dict(Any(), Any())

    # Private methods #########################################################

    def _get_running(self):
        return self.state == RUNNING

    def _get_stopped(self):
        return self.state == STOPPED

    def _state_changed(self, old_state, new_state):
        old_running = old_state == RUNNING
        new_running = new_state == RUNNING
        if old_running != new_running:
            self.trait_property_changed("running", old_running, new_running)

        old_stopped = old_state == STOPPED
        new_stopped = new_state == STOPPED
        if old_stopped != new_stopped:
            self.trait_property_changed("stopped", old_stopped, new_stopped)

    def __message_router_default(self):
        # Toolkit-specific message router.
        router = self._context.message_router()
        router.connect()
        self._have_message_router = True
        return router

    def __context_default(self):
        # By default, we use multithreading
        from traits_futures.multithreading_context import MultithreadingContext

        context = MultithreadingContext()
        self._own_context = True
        return context

    @on_trait_change("_message_router:receiver_done")
    def _remove_future(self, receiver):
        self._wrappers.pop(receiver)
        # If we're in STOPPING state and the last future has just exited,
        # go to STOPPED state.
        if self.state == STOPPING and not self._wrappers:
            self._stop()

    def _stop(self):
        """
        Go to STOPPED state, and shut down the worker pool if we own it.
        """
        assert self.state == STOPPING

        if self._have_message_router:
            self._message_router.disconnect()
            self._message_router = None

        if self._own_worker_pool:
            self._worker_pool.shutdown()
        self._worker_pool = None

        if self._own_context:
            self._context.close()
        self._context = None
        self.state = STOPPED
