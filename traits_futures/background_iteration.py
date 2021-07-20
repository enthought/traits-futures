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
Background task that sends results from an iteration.
"""

from traits.api import Callable, Dict, Event, HasStrictTraits, Str, Tuple

from traits_futures.base_future import BaseFuture, BaseTask, TaskCancelled
from traits_futures.i_task_specification import ITaskSpecification

#: Message sent whenever the iteration yields a result.
#: The message argument is the result generated.
GENERATED = "generated"


class IterationTask(BaseTask):
    """
    Iteration to be executed in the background.
    """

    def __init__(self, callable, args, kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def run(self):
        iterable = iter(self.callable(*self.args, **self.kwargs))

        while True:
            if self.cancelled():
                raise TaskCancelled

            try:
                result = next(iterable)
            except StopIteration as e:
                # If the iteration returned a value, the StopIteration
                # exception carries that value. Return it.
                return e.value

            self.send(GENERATED, result)
            # Don't keep a reference around until the next iteration.
            del result


class IterationFuture(BaseFuture):
    """
    Foreground representation of an iteration executing in the background.
    """

    #: Event fired whenever a result arrives from the background
    #: iteration.
    result_event = Event()

    # Private methods #########################################################

    def _process_generated(self, result):
        self.result_event = result


@ITaskSpecification.register
class BackgroundIteration(HasStrictTraits):
    """
    Object representing the background iteration to be executed.
    """

    #: The callable to be executed. This should return something iterable.
    callable = Callable()

    #: Positional arguments to be passed to the callable.
    args = Tuple()

    #: Named arguments to be passed to the callable.
    kwargs = Dict(Str())

    def future(self, cancel):
        """
        Return a Future for the background task.

        Parameters
        ----------
        cancel
            Zero-argument callable, returning no useful result. The returned
            future's ``cancel`` method should call this to request cancellation
            of the associated background task.

        Returns
        -------
        future : IterationFuture
            Future object that can be used to monitor the status of the
            background task.
        """
        return IterationFuture(_cancel=cancel)

    def task(self):
        """
        Return a background callable for this task specification.

        Returns
        -------
        task : IterationTask
            Callable accepting arguments ``send`` and ``cancelled``. The
            callable can use ``send`` to send messages and ``cancelled`` to
            check whether cancellation has been requested.
        """
        return IterationTask(
            callable=self.callable,
            args=self.args,
            kwargs=self.kwargs,
        )


def submit_iteration(executor, callable, *args, **kwargs):
    """
    Submit an iteration to an executor.

    Parameters
    ----------
    executor : TraitsExecutor
        Executor to submit the task to. This argument should always be
        passed by position rather than by name. Future versions of the library
        may enforce this restriction.
    callable
        Callable returning an iterator when called with the given arguments.
        This argument should always be passed by position rather than by name.
        Future versions of the library may enforce this restriction.
    *args
        Positional arguments to pass to the callable.
    **kwargs
        Named arguments to pass to the callable.

    Returns
    -------
    future : IterationFuture
        Object representing the state of the background iteration.
    """
    task = BackgroundIteration(callable=callable, args=args, kwargs=kwargs)
    return executor.submit(task)
