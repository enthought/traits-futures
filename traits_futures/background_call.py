# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Background task consisting of a simple callable.
"""
from traits.api import (
    Any,
    Bool,
    Callable,
    Dict,
    HasStrictTraits,
    Str,
    Tuple,
)

from traits_futures.base_future import BaseFuture
from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import (
    CANCELLING,
    DONE,
    EXECUTING,
)
from traits_futures.i_job_specification import IJobSpecification

# The background task sends either a "RAISED" message or a "RETURNED" message.

#: Call failed with an exception. Argument gives exception information.
RAISED = "raised"

#: Call succeeded and returned a result. Argument is the result.
RETURNED = "returned"


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
        try:
            result = self.callable(*self.args, **self.kwargs)
        except BaseException as e:
            send(RAISED, marshal_exception(e))
        else:
            send(RETURNED, result)


# CallFuture states. These represent the future's current
# state of knowledge of the background task. A task starts out
# in WAITING state and ends in one of the two final states
# DONE OR CANCELLED. The possible progressions of states are:
#
# WAITING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> CANCELLING -> CANCELLED
# WAITING -> EXECUTING -> DONE


class CallFuture(BaseFuture):
    """
    Object representing the front-end handle to a background call.
    """

    @property
    def ok(self):
        """
        Boolean indicating whether the background job completed successfully.

        Not available for cancelled or pending jobs.
        """
        if self.state != DONE:
            raise AttributeError(
                "Background job was cancelled, or has not yet completed."
            )
        return self._have_result

    @property
    def result(self):
        """
        Result of the background call. Raises an ``AttributeError`` on access
        if no result is available (because the background call failed, was
        cancelled, or has not yet completed).

        Note: this is deliberately a regular Python property rather than a
        Trait, to discourage users from attaching Traits listeners to
        it. Listen to the state or its derived traits instead.
        """
        if not self._have_result:
            raise AttributeError("No result available for this call.")
        return self._result

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

    #: Boolean indicating whether we have a result available.
    _have_result = Bool(False)

    #: Result from the background task.
    _result = Any()

    #: Boolean indicating whether we have exception information available.
    _have_exception = Bool(False)

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    def _process_raised(self, exception_info):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._have_exception = True
            self._exception = exception_info

    def _process_returned(self, result):
        assert self.state in (EXECUTING, CANCELLING)
        if self.state == EXECUTING:
            self._have_result = True
            self._result = result


@IJobSpecification.register
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
        return CallBackgroundTask(
            callable=self.callable,
            args=self.args,
            # Convert TraitsDict to a regular dict
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
        future : CallFuture
            Foreground object representing the state of the running
            calculation.
        """
        return CallFuture(_cancel=cancel, _message_receiver=message_receiver)
