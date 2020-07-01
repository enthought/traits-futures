# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Background task that sends results from an iteration.
"""
import types

from traits.api import (
    Any,
    Bool,
    Callable,
    Dict,
    Event,
    HasStrictTraits,
    Str,
    Tuple,
)

from traits_futures.base_future import BaseFuture
from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLING,
    COMPLETED,
    EXECUTING,
)
from traits_futures.i_job_specification import IJobSpecification


# Message types for messages from IterationBackgroundTask to IterationFuture.
# The background iteration will emit exactly one of the following
# sequences of message types, where GENERATED* indicates zero-or-more
# GENERATED messages.
#
#   [RAISED]
#   [GENERATED*, RAISED]
#   [GENERATED*]

#: Iteration failed with an exception, or there was
#: an exception on creation of the iterator. Argument gives
#: exception information.
RAISED = "raised"

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
        try:
            iterable = iter(self.callable(*self.args, **self.kwargs))
        except BaseException as e:
            send(RAISED, marshal_exception(e))
            return

        while not cancelled():
            try:
                result = next(iterable)
            except StopIteration:
                break
            except BaseException as e:
                send(RAISED, marshal_exception(e))
                break
            else:
                send(GENERATED, result)
                # Don't keep a reference around until the next iteration.
                del result

        # If the iterable is a generator, close it. This ensures that any
        # cleanup in the generator function (e.g., as a result of leaving a
        # with block, or executing a finally clause) occurs promptly.
        if isinstance(iterable, types.GeneratorType):
            iterable.close()


# IterationFuture states. These represent the futures' current state of
# knowledge of the background iteration. An iteration starts out in EXECUTING
# state and ends with one of COMPLETED or CANCELLED. The possible
# progressions of states are:
#
# EXECUTING -> CANCELLING -> CANCELLED
# EXECUTING -> COMPLETED
#
# The ``result`` trait will only be fired when the state is EXECUTING;
# no results events will be fired after cancelling.


class IterationFuture(BaseFuture):
    """
    Foreground representation of an iteration executing in the
    background.
    """

    #: Event fired whenever a result arrives from the background
    #: iteration.
    result_event = Event(Any())

    @property
    def ok(self):
        """
        Boolean indicating whether the background job completed successfully.

        Not available for cancelled or pending jobs.
        """
        if self.state != COMPLETED:
            raise AttributeError(
                "Job has not yet completed, or was cancelled. "
                "Job status is {}".format(self.state)
            )

        return self._ok

    @property
    def exception(self):
        """
        Information about any exception raised by the background call. Raises
        an ``AttributeError`` on access if no exception was raised (because the
        call succeeded, was cancelled, or has not yet completed).
        """
        if self.state != COMPLETED:
            raise AttributeError(
                "Job has not yet completed, or was cancelled. "
                "Job status is {}".format(self.state)
            )

        if self._ok:
            raise AttributeError(
                "This job completed without raising an exception. "
            )

        return self._exception

    # Private traits ##########################################################

    #: Boolean indicating whether the job completed successfully.
    _ok = Bool(True)

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    def _process_raised(self, exception_info):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._ok = False
            self._exception = exception_info

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

    # XXX Move the pre-run cancel check to the background job wrapper.

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
            callable=self.callable,
            args=self.args,
            # Convert TraitsDict to a regular dict.
            # XXX Perhaps we should just be using `instance(dict)` in
            # the first place? We have no need to listen to the `kwargs`
            # attribute.
            kwargs=dict(self.kwargs),
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
        return IterationFuture(_cancel=cancel, _receiver=receiver,)


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
    task = BackgroundIteration(callable=callable, args=args, kwargs=kwargs,)
    return executor.submit(task)
