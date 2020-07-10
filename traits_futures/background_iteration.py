# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Background task that sends results from an iteration.
"""

from traits.api import (
    Any,
    Callable,
    Dict,
    Event,
    HasStrictTraits,
    Str,
    Tuple,
)

from traits_futures.base_future import BaseFuture
from traits_futures.future_states import (
    CANCELLING,
    EXECUTING,
)
from traits_futures.i_job_specification import IJobSpecification


# Additional message types for background iterations.

#: Message sent whenever the iteration yields a result.
#: Argument is the result generated.
GENERATED = "generated"


class IterationBackgroundTask:
    """
    Iteration to be executed in the background.
    """

    def __init__(self, callable, args, kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def __call__(self, send, cancelled):
        iterable = iter(self.callable(*self.args, **self.kwargs))

        while not cancelled():
            try:
                result = next(iterable)
            except StopIteration as e:
                # The StopIteration exception potentially carries a value.
                # Return it.
                # XXX Needs tests!
                return e.value
            else:
                send(GENERATED, result)
                # Don't keep a reference around until the next iteration.
                del result


class IterationFuture(BaseFuture):
    """
    Foreground representation of an iteration executing in the
    background.
    """

    #: Event fired whenever a result arrives from the background
    #: iteration.
    result_event = Event(Any())

    # Private methods #########################################################

    def _process_generated(self, result):
        assert self.state in (EXECUTING, CANCELLING)
        # Any results arriving after a cancellation request are ignored.
        if self.state == EXECUTING:
            self.result_event = result


@IJobSpecification.register
class BackgroundIteration(HasStrictTraits):
    """
    Object representing the background iteration to be executed.
    """

    #: The callable to be executed. This should return something iterable.
    callable = Callable()

    #: Positional arguments to be passed to the callable.
    args = Tuple()

    #: Named arguments to be passed to the callable.
    kwargs = Dict(Str(), Any())

    def background_job(self):
        """
        Return a background callable for this job specification.

        Returns
        -------
        background : callable
            Callable accepting arguments ``sender`` and ``cancelled``, and
            returning nothing. The callable will use ``sender`` to send
            messages and ``cancelled` to check whether the job has been
            cancelled.
        """
        return IterationBackgroundTask(
            callable=self.callable, args=self.args, kwargs=self.kwargs.copy(),
        )

    def future(self, cancel, receiver):
        """
        Return a future for a background job.

        Parameters
        ----------
        cancel : callable
            Callable called with no arguments to request cancellation
            of the background task.
        receiver : MessageReceiver
            Object that remains in the main thread and receives messages sent
            by the message sender. This is a HasTraits subclass with
            a 'message' Event trait that can be listened to for arriving
            messages.

        Returns
        -------
        future : IterationFuture
            Foreground object representing the state of the running
            calculation.
        """
        return IterationFuture(_cancel=cancel, _receiver=receiver)


def submit_iteration(executor, callable, *args, **kwargs):
    """
    Convenience function to submit a background iteration to an executor.

    Parameters
    ----------
    executor : TraitsExecutor
        Executor to submit the call to.
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
    task = BackgroundIteration(callable=callable, args=args, kwargs=kwargs)
    return executor.submit(task)
