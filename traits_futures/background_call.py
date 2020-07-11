# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Background task consisting of a simple callable.
"""
from traits.api import (
    Any,
    Callable,
    Dict,
    HasStrictTraits,
    Str,
    Tuple,
)

from traits_futures.base_future import BaseFuture
from traits_futures.i_task_specification import ITaskSpecification


class CallBackgroundTask:
    """
    Wrapper around the actual callable to be run. This wrapper provides the
    task that will be submitted to the concurrent.futures executor
    """

    def __init__(self, callable, args, kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self, send, cancelled):
        return self.callable(*self.args, **self.kwargs)


class CallFuture(BaseFuture):
    """
    Object representing the front-end handle to a background call.
    """


@ITaskSpecification.register
class BackgroundCall(HasStrictTraits):
    """
    Object representing the background call to be executed.
    """

    #: The callable to be executed.
    callable = Callable()

    #: Positional arguments to be passed to the callable.
    args = Tuple()

    #: Named arguments to be passed to the callable.
    kwargs = Dict(Str(), Any())

    def background_task(self):
        """
        Return a background callable for this task specification.

        Returns
        -------
        background : callable
            Callable accepting arguments ``send`` and ``cancelled``. The
            callable can use ``send`` to send messages and ``cancelled` to
            check whether cancellation has been requested.
        """
        return CallBackgroundTask(
            callable=self.callable, args=self.args, kwargs=self.kwargs.copy(),
        )

    def future(self):
        """
        Return a future for a background task.

        Returns
        -------
        future : CallFuture
            Foreground object representing the state of the running
            calculation.
        """
        return CallFuture()


def submit_call(executor, callable, *args, **kwargs):
    """
    Convenience function to submit a background call to an executor.

    Parameters
    ----------
    executor : TraitsExecutor
        Executor to submit the call to.
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
    task = BackgroundCall(callable=callable, args=args, kwargs=kwargs)
    return executor.submit(task)
