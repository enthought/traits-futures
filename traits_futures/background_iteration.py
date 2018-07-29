"""
Background task that sends results from an iteration.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits.api import (
    Any, Bool, Callable, Dict, Event, HasStrictTraits, Instance,
    on_trait_change, Property, Str, Tuple)

from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLED, CANCELLING, EXECUTING, FAILED, COMPLETED, WAITING,
    FINAL_STATES, CANCELLABLE_STATES, FutureState)

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


class IterationBackgroundTask(object):
    """
    Iteration to be executed in the background.
    """
    def __init__(self, callable, args, kwargs, message_sender, cancel_event):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.message_sender = message_sender
        self.cancel_event = cancel_event

    def __call__(self):
        with self.message_sender:
            if self.cancel_event.is_set():
                self.send(INTERRUPTED)
                return

            try:
                iterable = iter(self.callable(*self.args, **self.kwargs))
            except BaseException as e:
                self.send(RAISED, marshal_exception(e))
                return

            self.send(STARTED)

            while True:
                if self.cancel_event.is_set():
                    self.send(INTERRUPTED)
                    break

                try:
                    result = next(iterable)
                except StopIteration:
                    self.send(EXHAUSTED)
                    break
                except BaseException as e:
                    self.send(RAISED, marshal_exception(e))
                    break
                else:
                    self.send(GENERATED, result)

    def send(self, message_type, message_args=None):
        """
        Send a message to the foreground controller.
        """
        self.message_sender.send((message_type, message_args))


# IterationFuture states. These represent the futures' current state of
# knowledge of the background iteration. An iteration starts out in WAITING
# state and ends with one of COMPLETED, FAILED or CANCELLED. The possible
# progressions of states are:
#
# WAITING -> FAILED
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

    #: True if we've received the final message from the background iteration,
    #: else False. `True` indicates either that the background iteration
    #: succeeded, or that it raised, or that it was cancelled.
    done = Property(Bool, depends_on='state')

    #: True if this task can be cancelled, else False.
    cancellable = Property(Bool, depends_on='state')

    #: Event fired whenever a result arrives from the background
    #: iteration.
    result = Event(Any)

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
        self._cancel_event.set()
        self.state = CANCELLING

    # Private traits ##########################################################

    #: Private event used to request cancellation of this task. Users
    #: should call the cancel() method instead of using this event.
    _cancel_event = Any

    #: Exception information from the background task.
    _exception = Tuple(Str, Str, Str)

    #: Object that receives messages from the background task.
    _message_receiver = Instance(HasStrictTraits)

    # Private methods #########################################################

    @on_trait_change('_message_receiver:message')
    def _process_message(self, message):
        message_type, message_arg = message
        method_name = "_process_{}".format(message_type)
        getattr(self, method_name)(message_arg)

    def _process_interrupted(self, arg):
        assert self.state in (CANCELLING,)
        self.state = CANCELLED

    def _process_started(self, arg):
        assert self.state in (WAITING, CANCELLING)
        if self.state == WAITING:
            self.state = EXECUTING

    def _process_raised(self, arg):
        assert self.state in (WAITING, EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._exception = arg
            self.state = FAILED
        elif self.state == WAITING:
            self._exception = arg
            self.state = FAILED
        else:
            # Don't record the exception if the job was already cancelled.
            self.state = CANCELLED

    def _process_exhausted(self, arg):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self.state = COMPLETED
        else:
            self.state = CANCELLED

    def _process_generated(self, arg):
        assert self.state in (EXECUTING, CANCELLING)
        # Any results arriving after a cancellation request are ignored.
        if self.state == EXECUTING:
            self.result = arg

    def _get_cancellable(self):
        return self.state in CANCELLABLE_STATES

    def _get_done(self):
        return self.state in FINAL_STATES


class BackgroundIteration(HasStrictTraits):
    """
    Object representing the background iteration to be executed.
    """
    #: The callable to be executed. This should return something iterable.
    callable = Callable

    #: Positional arguments to be passed to the callable.
    args = Tuple

    #: Named arguments to be passed to the callable.
    kwargs = Dict(Str, Any)

    def prepare(self, cancel_event, message_sender, message_receiver):
        """
        Prepare the background iteration for running.

        Returns a pair (future, background_iteration), where
        the future acts as a handle for task cancellation, etc.,
        and the background_iteration is a callable to be executed
        in the background.
        """
        future = IterationFuture(
            _cancel_event=cancel_event,
            _message_receiver=message_receiver,
        )
        runner = IterationBackgroundTask(
            callable=self.callable,
            args=self.args,
            # Convert TraitsDict to a regular dict
            kwargs=dict(self.kwargs),
            message_sender=message_sender,
            cancel_event=cancel_event,
        )
        return future, runner
