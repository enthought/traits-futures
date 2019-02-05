# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Main-thread executor for submission of background tasks.
"""

from __future__ import absolute_import, print_function, unicode_literals

import concurrent.futures
import threading

from traits.api import (
    Bool, Enum, HasStrictTraits, HasTraits, Instance, on_trait_change,
    Property, Set)

from traits_futures.background_call import BackgroundCall
from traits_futures.background_iteration import BackgroundIteration
from traits_futures.background_progress import BackgroundProgress
from traits_futures.toolkit_support import message_router_class


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
    """
    #: Current state of this executor.
    state = ExecutorState

    #: Derived state: true if this executor is running; False if it's
    #: stopped or stopping.
    running = Property(Bool())

    #: Derived state: true if this executor is stopped and it's safe
    #: to dispose of related resources (like the thread pool).
    stopped = Property(Bool())

    def __init__(self, thread_pool=None, **traits):
        super(TraitsExecutor, self).__init__(**traits)

        if thread_pool is None:
            self._thread_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=4)
            self._own_thread_pool = True
        else:
            self._thread_pool = thread_pool
            self._own_thread_pool = False

    def submit_call(self, callable, *args, **kwargs):
        """
        Convenience function to submit a background call.

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
        task = BackgroundCall(
            callable=callable,
            args=args,
            kwargs=kwargs,
        )
        return self.submit(task)

    def submit_iteration(self, callable, *args, **kwargs):
        """
        Convenience function to submit a background iteration.

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
        task = BackgroundIteration(
            callable=callable,
            args=args,
            kwargs=kwargs,
        )
        return self.submit(task)

    def submit_progress(self, callable, *args, **kwargs):
        """
        Convenience function to submit a background progress call.

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
        task = BackgroundProgress(
            callable=callable,
            args=args,
            kwargs=kwargs,
        )
        return self.submit(task)

    def submit(self, task):
        """
        Submit a task to the executor, and return the corresponding future.

        Parameters
        ----------
        task : BackgroundCall, BackgroundIteration or BackgroundProgress
            The task to be executed.

        Returns
        -------
        future : CallFuture, IterationFuture or ProgressFuture
            Future for this task.
        """
        if not self.running:
            raise RuntimeError("Can't submit task unless executor is running.")

        sender, receiver = self._message_router.pipe()
        future, runner = task.future_and_callable(
            cancel_event=threading.Event(),
            message_sender=sender,
            message_receiver=receiver,
        )
        self._thread_pool.submit(runner)
        self._futures.add(future)
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
        for future in self._futures:
            if future.cancellable:
                future.cancel()

        if not self._futures:
            self._stop()

    # Private traits ##########################################################

    #: concurrent.futures.Executor instance providing the thread pool.
    _thread_pool = Instance(concurrent.futures.Executor)

    #: True if we own this thread pool (and are therefore responsible
    #: for shutting it down), else False.
    _own_thread_pool = Bool()

    #: Router providing message connections between background tasks
    #: and foreground futures.
    _message_router = Instance(HasTraits)

    #: Currently executing futures.
    _futures = Set()

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
        class_ = message_router_class()
        return class_()

    @on_trait_change('_futures:_exiting')
    def _remove_future(self, future, name, new):
        self._futures.remove(future)
        # If we're in STOPPING state and the last future has just exited,
        # go to STOPPED state.
        if self.state == STOPPING and not self._futures:
            self._stop()

    def _stop(self):
        """
        Go to STOPPED state, and shut down the thread pool if we own it.
        """
        assert self.state == STOPPING
        if self._own_thread_pool:
            self._thread_pool.shutdown()
        self._thread_pool = None
        self.state = STOPPED
