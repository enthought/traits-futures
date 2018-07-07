from traits.api import (
    Any, Bool, Callable, Dict, Enum, Event, HasStrictTraits, Int, Property,
    Str, Tuple,
)

from traits_futures.exception_handling import marshal_exception

# Messages from the runner to the future
# --------------------------------------

#: Message sent after the iterator is created and
#: before the iteration is started. No payload.
STARTING = "Starting"

#: Message sent whenever the iteration yields a result.
#: Payload is the result.
RESULT = "Result"

#: Message sent on discovering that cancellation has
#: been requested.
INTERRUPTED = "Interrupted"

#: Message sent whenever an iteration fails with an
#: exception. This message is also sent if an exception
#: occurs on creation of the iterator. In either case,
#: the payload carries the marshalled exception details.
RAISED = "Raised"

#: Message sent on completion of the iteration.
#: No payload.
EXHAUSTED = "Exhausted"

# Future states
# -------------

#: Iteration completed without any error.
COMPLETED = "Completed"

#: User has requested cancellation of the iteration, but
#: that request has not yet been processed by the background
#: iterator.
CANCELLING = "Cancelling"

#: Iterator has been cancelled.
CANCELLED = "Cancelled"

#: Iteration has started execution (i.e., is no
#: longer waiting for an executor worker).
EXECUTING = "Executing"

#: Exception raised during iteration.
FAILED = "Failed"

#: Exception raised when setting up the iteration (e.g., because
#: the callable given didn't produce a valid iterable when called)
SETUP_FAILED = "Setup failed"

#: Background job is queued, awaiting execution.
WAITING = "Waiting"

#: Final states. If the future is in one of these states,
#: no more messages will be received from the background job.
FINAL_STATES = {CANCELLED, COMPLETED, SETUP_FAILED, FAILED}


class IterationFuture(HasStrictTraits):
    """
    Foreground representation of an iteration executing in the
    background.
    """
    #: The current state of this job.
    state = Enum(
        WAITING, EXECUTING,
        FAILED, SETUP_FAILED, COMPLETED,
        CANCELLING, CANCELLED)

    #: The id of this job.
    job_id = Int()

    #: Event used to request cancellation of this job.
    cancel_event = Any()

    #: Event fired whenever a result arrives from the background
    #: iteration.
    result = Event(Any)

    #: Value set on exception, either during setting up
    #: the iterator or during the iteration itself. Use the
    #: state to distinguish these two cases if necessary.
    exception = Any

    #: Boolean indicating whether the current job can be
    #: cancelled. A completed or already cancelled job can't
    #: be cancelled.
    cancellable = Property(Bool, depends_on="state")

    #: Boolean indicating whether the current job has
    #: completed (either through an error, through being cancelled,
    #: or through completing normally)
    completed = Property(Bool, depends_on="state")

    def cancel(self):
        """
        Method called from the main thread to request cancellation
        of the background job.
        """
        # In the interests of catching coding errors early in client
        # code, we're strict about what states we allow cancellation
        # from. Some applications may want to weaken the error below
        # to a warning, or just do nothing on an invalid cancellation.
        if self.cancellable:
            self.state = CANCELLING
            self.cancel_event.set()
        else:
            raise RuntimeError("Can only cancel a waiting or executing job.")

    def process_message(self, message):
        """
        Process a message from the background job.

        Return True if this message represents the final
        communication from the background job, and False otherwise.
        """
        msg_type, msg_args = message
        if msg_type == STARTING:
            assert self.state in (WAITING, CANCELLING)
            if self.state == WAITING:
                self.state = EXECUTING

        elif msg_type == EXHAUSTED:
            assert self.state in (EXECUTING, CANCELLING)
            if self.state == CANCELLING:
                self.state = CANCELLED
            else:
                self.state = COMPLETED

        elif msg_type == RESULT:
            assert self.state in (EXECUTING, CANCELLING)
            # Results arriving after cancellation are ignored.
            if self.state == EXECUTING:
                self.result = msg_args

        elif msg_type == RAISED:
            assert self.state in (WAITING, EXECUTING, CANCELLING)
            if self.state == WAITING:
                self.exception = msg_args
                self.state = SETUP_FAILED
            elif self.state == EXECUTING:
                self.exception = msg_args
                self.state = FAILED
            else:
                # Don't record the exception if the job
                # was already cancelled.
                self.state = CANCELLED

        elif msg_type == INTERRUPTED:
            assert self.state == CANCELLING
            self.state = CANCELLED

        else:
            raise RuntimeError(
                "Unrecognised message type: {}".format(msg_type))

        return self.completed

    def _get_cancellable(self):
        return self.state in {WAITING, EXECUTING}

    def _get_completed(self):
        return self.state in FINAL_STATES


class IterationRunner(object):
    """
    Callable to be executed in the background.
    """
    def __init__(
            self, job_id, callable, args, kwargs,
            results_queue, cancel_event):
        self.job_id = job_id
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.results_queue = results_queue
        self.cancel_event = cancel_event

    def __call__(self):
        if self.cancel_event.is_set():
            self.send(INTERRUPTED)
            return

        try:
            iterable = iter(self.callable(*self.args, **self.kwargs))
        except BaseException as e:
            self.send(RAISED, marshal_exception(e))
            return

        self.send(STARTING)

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
                self.send(RESULT, result)

    def send(self, message_type, message_args=None):
        self.results_queue.put((self.job_id, (message_type, message_args)))


class BackgroundIteration(HasStrictTraits):
    #: The callable to be executed. This should return
    #: something iterable.
    callable = Callable

    #: Positional arguments to be passed to the callable.
    args = Tuple

    #: Keyword arguments to be passed to the callable.
    kwargs = Dict(Str, Any)

    def prepare(self, job_id, cancel_event, results_queue):
        future = IterationFuture(
            job_id=job_id,
            cancel_event=cancel_event,
        )
        runner = IterationRunner(
            job_id=job_id,
            cancel_event=cancel_event,
            results_queue=results_queue,
            callable=self.callable,
            args=self.args,
            kwargs=dict(self.kwargs),
        )
        return future, runner


def background_iteration(callable, *args, **kwargs):
    """
    Convenience fucntion for creating BackgroundIteration objects.
    """
    return BackgroundIteration(callable=callable, args=args, kwargs=kwargs)
