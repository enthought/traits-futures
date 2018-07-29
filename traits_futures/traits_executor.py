# Main-thread controller for background tasks.
from __future__ import absolute_import, print_function, unicode_literals

import threading

import concurrent.futures

from traits.api import Any, Enum, HasStrictTraits, Instance

from traits_futures.background_call import BackgroundCall
from traits_futures.background_iteration import BackgroundIteration
from traits_futures.qt_message_router import QtMessageRouter


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

    #: concurrent.futures.Executor instance providing the thread pool.
    thread_pool = Instance(concurrent.futures.Executor)

    #: Endpoint for receiving messages.
    _message_router = Any

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

    def submit(self, task):
        """
        Submit a task to the executor, and return the corresponding future.

        Parameters
        ----------
        task : BackgroundCall or BackgroundIteration
            The task to be executed.

        Returns
        -------
        future : CallFuture or IterationFuture
            Future for this task.
        """
        sender, receiver = self._message_router.pipe()
        future, runner = task.future_and_callable(
            cancel_event=threading.Event(),
            message_sender=sender,
            message_receiver=receiver,
        )
        self.thread_pool.submit(runner)
        return future

    def _thread_pool_default(self):
        return concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def __message_router_default(self):
        return QtMessageRouter()
