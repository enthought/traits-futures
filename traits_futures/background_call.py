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
from traits_futures.future_states import CANCELLING, DONE
from traits_futures.i_job_specification import IJobSpecification

# The background task sends either a "RAISED" message or a "RETURNED" message
# on completion.

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


class CallFuture(BaseFuture):
    """
    Object representing the front-end handle to a background call.
    """

    @property
    def ok(self):
        """
        Boolean indicating whether the background job completed successfully.
        This attribute is only available for a job in DONE state.

        Returns
        -------
        ok : bool
            True if the job completed successfully, in which case the result
            is available from the .result attribute. False if the job
            raised an exception.

        Raises
        ------
        AttributeError
            If the job is still executing, or was cancelled.
        """
        if self.state != DONE:
            raise AttributeError(
                "Job has not yet completed, or was cancelled."
                "Job status is {}".format(self.state)
            )

        return self._ok

    @property
    def result(self):
        """
        Result of the background call. This is only available if:

        - the state of the future is DONE
        - the call completed normally, without raising

        Returns
        -------
        result : object
            The result obtained from the background call.

        Raises
        ------
        AttributeError
            If the job is still executing, or was cancelled, or raised an
            exception instead of returning a result.
        """
        if self.state != DONE:
            raise AttributeError(
                "Job has not yet completed, or was cancelled. "
                "Job status is {}".format(self.state)
            )

        if not self._ok:
            raise AttributeError(
                "No result available; job raised an exception. "
                "Exception details are in the 'exception' attribute."
            )

        return self._result

    @property
    def exception(self):
        """
        Information about any exception raised by the background call. Raises
        an ``AttributeError`` on access if no exception was raised (because the
        call succeeded, was cancelled, or has not yet completed).

        Returns
        -------
        exc_info : tuple(str, str, str)
            Tuple containing marshalled exception information.

        Raises
        ------
        AttributeError
            If the job is still executing, or was cancelled, or completed
            without raising an exception.
        """
        if self.state != DONE:
            raise AttributeError(
                "Job has not yet completed, or was cancelled. "
                "Job status is {}".format(self.state)
            )

        if self._ok:
            raise AttributeError(
                "This job completed without raising an exception. "
                "See the 'result' attribute for the job result."
            )

        return self._exception

    # Private traits ##########################################################

    #: Boolean indicating whether the job completed successfully.
    _ok = Bool()

    #: Result from the background task.
    _result = Any()

    #: Exception information from the background task.
    _exception = Tuple(Str(), Str(), Str())

    # Private methods #########################################################

    # Process the messages from the background call.

    def _process_raised(self, exception_info):
        if self.state != CANCELLING:
            self._exception = exception_info
            self._ok = False

    def _process_returned(self, result):
        if self.state != CANCELLING:
            self._result = result
            self._ok = True


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
        future : CallFuture
            Foreground object representing the state of the running
            calculation.
        """
        return CallFuture(_cancel=cancel, _receiver=receiver)
