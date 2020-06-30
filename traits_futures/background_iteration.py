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
    CANCELLED,
    CANCELLING,
    EXECUTING,
    FAILED,
    COMPLETED,
    WAITING,
)
from traits_futures.i_job_specification import IJobSpecification


# Message types for messages from IterationBackgroundTask to IterationFuture.
# The background iteration will emit exactly one of the following
# sequences of message types, where GENERATED* indicates zero-or-more
# GENERATED messages.
#
#   [INTERRUPTED]
#   [RAISED]
#   [STARTED, GENERATED*, INTERRUPTED]
#   [STARTED, GENERATED*, RAISED]
#   [STARTED, GENERATED*, EXHAUSTED]

#: Iteration was cancelled either before it started or during the
#: iteration. No arguments.
INTERRUPTED = "interrupted"

#: Iteration failed with an exception, or there was
#: an exception on creation of the iterator. Argument gives
#: exception information.
RAISED = "raised"

#: Iteration completed normally. No arguments.
EXHAUSTED = "exhausted"

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

        while True:
            if cancelled():
                message, message_args = INTERRUPTED, None
                break

            try:
                result = next(iterable)
            except StopIteration:
                message, message_args = EXHAUSTED, None
                break
            except BaseException as e:
                message, message_args = RAISED, marshal_exception(e)
                break
            else:
                send(GENERATED, result)
                # Delete now, else we'll hang on to the reference to this
                # result until the next iteration, which could be some
                # arbitrary time in the future.
                del result

        # If the iterable is a generator, close it before we send the final
        # message. This ensures that any cleanup in the generator function
        # (e.g., as a result of leaving a with block, or executing a
        # finally clause) occurs promptly.
        if isinstance(iterable, types.GeneratorType):
            iterable.close()
        # Belt and braces: also delete the reference to the iterable.
        del iterable

        send(message, message_args)


# IterationFuture states. These represent the futures' current state of
# knowledge of the background iteration. An iteration starts out in WAITING
# state and ends with one of COMPLETED, FAILED or CANCELLED. The possible
# progressions of states are:
#
# WAITING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> FAILED
# WAITING -> EXECUTING -> COMPLETED
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
    def exception(self):
        """
        Information about any exception raised by the background call. Raises
        an ``AttributeError`` on access if no exception was raised (because the
        call succeeded, was cancelled, or has not yet completed).

        Note: this is deliberately a regular Python property rather than a
        Trait, to discourage users from attaching Traits listeners to
        it. Listen to the state or its derived traits instead.
        """
        if not self._have_exception:
            raise AttributeError("No exception has been raised for this call.")
        return self._exception

    # Private traits ##########################################################

    #: Boolean indicating whether we have exception information available.
    _have_exception = Bool(False)

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    def _process_raised(self, exception_info):
        assert self.state in (WAITING, EXECUTING, CANCELLING)
        if self.state in (EXECUTING, WAITING):
            self._have_exception = True
            self._exception = exception_info
            self.state = FAILED
        else:
            # Don't record the exception if the job was already cancelled.
            self.state = CANCELLED

    def _process_exhausted(self, none):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self.state = COMPLETED
        else:
            self.state = CANCELLED

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

    def future(self, cancel, message_receiver):
        """
        Return a future for a background job.

        Parameters
        ----------
        cancel : callable
            Callable called with no arguments to request cancellation
            of the background task.
        message_receiver : MessageReceiver
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
        return IterationFuture(
            _cancel=cancel, _message_receiver=message_receiver,
        )
