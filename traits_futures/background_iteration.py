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
    HasTraits,
    Instance,
    on_trait_change,
    Property,
    Str,
    Tuple,
)

from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLED,
    CANCELLING,
    EXECUTING,
    FAILED,
    COMPLETED,
    WAITING,
    CANCELLABLE_STATES,
    DONE_STATES,
    FutureState,
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

#: Iteration started executing. No arguments.
STARTED = "started"

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
        send(STARTED)
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


class IterationFuture(HasStrictTraits):
    """
    Foreground representation of an iteration executing in the
    background.
    """

    #: The state of the background iteration, to the best of the knowledge of
    #: this future.
    state = FutureState

    #: True if this task can be cancelled, else False.
    cancellable = Property(Bool())

    #: True if we've received the final message from the background iteration,
    #: else False. `True` indicates either that the background iteration
    #: succeeded, or that it raised, or that it was cancelled.
    done = Property(Bool())

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
        if self.state != FAILED:
            raise AttributeError("No exception has been raised for this call.")
        return self._exception

    def cancel(self):
        """
        Method called from the main thread to request cancellation
        of the background job.
        """
        # In the interests of catching coding errors early in client
        # code, we're strict about what states we allow cancellation
        # from. Some applications may want to weaken the error below
        # to a warning, or just do nothing on an invalid cancellation.
        if not self.cancellable:
            raise RuntimeError("Can only cancel a queued or executing task.")
        self._cancel()
        self.state = CANCELLING

    # Private traits ##########################################################

    #: Callable called with no arguments to request cancellation of the
    #: background task.
    _cancel = Callable()

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    #: Object that receives messages from the background task.
    _message_receiver = Instance(HasTraits)

    # Private methods #########################################################

    @on_trait_change("_message_receiver:message")
    def _process_message(self, message):
        message_type, message_arg = message
        method_name = "_process_{}".format(message_type)
        getattr(self, method_name)(message_arg)

    def _process_interrupted(self, none):
        assert self.state in (CANCELLING,)
        self.state = CANCELLED

    def _process_started(self, none):
        assert self.state in (WAITING, CANCELLING)
        if self.state == WAITING:
            self.state = EXECUTING

    def _process_raised(self, exception_info):
        assert self.state in (WAITING, EXECUTING, CANCELLING)
        if self.state in (EXECUTING, WAITING):
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

    def _get_cancellable(self):
        return self.state in CANCELLABLE_STATES

    def _get_done(self):
        return self.state in DONE_STATES

    def _state_changed(self, old_state, new_state):
        old_cancellable = old_state in CANCELLABLE_STATES
        new_cancellable = new_state in CANCELLABLE_STATES
        if old_cancellable != new_cancellable:
            self.trait_property_changed(
                "cancellable", old_cancellable, new_cancellable
            )

        old_done = old_state in DONE_STATES
        new_done = new_state in DONE_STATES
        if old_done != new_done:
            self.trait_property_changed("done", old_done, new_done)


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
