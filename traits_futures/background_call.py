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
Background task consisting of a simple callable.
"""
from traits.api import Callable, Dict, HasStrictTraits, Str, Tuple

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
    kwargs = Dict(Str())

    def future(self):
        """
        Return a Future for the background task.

        Returns
        -------
        future : CallFuture
            Future object that can be used to monitor the status of the
            background task.
        """
        return CallFuture()

    def background_task(self):
        """
        Return a background callable for this task specification.

        Returns
        -------
        collections.abc.Callable
            Callable accepting arguments ``send`` and ``cancelled``. The
            callable can use ``send`` to send messages and ``cancelled`` to
            check whether cancellation has been requested.
        """
        return CallBackgroundTask(
            callable=self.callable,
            args=self.args,
            kwargs=self.kwargs.copy(),
        )


def submit_call(executor, callable, *args, **kwargs):
    """
    Convenience function to submit a background call to an executor.

    Parameters
    ----------
    executor : TraitsExecutor
        Executor to submit the task to.
    callable : collections.abc.Callable
        Callable to execute in the background.
    *args
        Positional arguments to pass to the callable.
    **kwargs
        Named arguments to pass to the callable.

    Returns
    -------
    future : CallFuture
        Object representing the state of the background call.
    """
    task = BackgroundCall(callable=callable, args=args, kwargs=kwargs)
    return executor.submit(task)
