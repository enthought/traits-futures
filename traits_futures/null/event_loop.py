"""
A bare-bones event loop that doesn't need any UI framework.
"""
# XXX Need method that runs until all event handlers removed.
# XXX Test coverage!


from __future__ import absolute_import, print_function, unicode_literals

import itertools
import time

from six.moves import queue

#: Event loop action: call with given arguments.
_CALL_ACTION = "call"

#: Event loop action: dispose of an async caller.
_CLOSE_ACTION = "close"

#: Event loop state: not currently running.
IDLE = "idle"

#: Event loop state: running.
RUNNING = "running"

#: Event loop state: asked to stop, but not yet stopped.
STOPPING = "stopping"


class AsyncCaller(object):
    """
    Object allowing asynchronous execution of a callable.

    This object is created in the main thread by the event_loop. It may
    then be passed to and used in a background thread if desired. The
    ``__call__`` and ``close`` methods should all be called from the
    same thread.
    """
    def __init__(self, event_queue, caller_id):
        #: The main event loop's queue.
        self._event_queue = event_queue
        #: Integer identifying this caller.
        self._caller_id = caller_id
        #: Boolean indicating whether this connection has been closed yet.
        self._closed = False

    def __call__(self, *args, **kwargs):
        """
        Request a call with the given arguments.

        The call returns immediately, and posts an event to the event
        queue. When that event is processed, the corresponding callable will be
        called with the given arguments.
        """
        if self._closed:
            raise RuntimeError("This AsyncCaller is closed.")
        self._event_queue.put((_CALL_ACTION, self._caller_id, args, kwargs))

    def close(self):
        """
        Remove any resources used by this caller.

        Used to indicate that no more calls will be made using this caller,
        so that the corresponding entry can be removed from the EventLoop's
        table of event handlers.
        """
        self._event_queue.put((_CLOSE_ACTION, self._caller_id))
        self._closed = True


class EventLoop(object):
    """
    A simple event loop that doesn't require any UI framework.

    This event loop has exactly one trick, and that's the ability
    to fire callables asynchronously.
    """
    def __init__(self):
        #: Action queue for the event loop.
        self._event_queue = queue.Queue()
        #: Currently registered handlers, indexed by integer id.
        self._event_handlers = {}
        #: Source of unique ids for handlers.
        self._caller_ids = itertools.count()
        #: Current state of this event loop; one of IDLE, RUNNING or STOPPING
        self.state = IDLE

    def start(self, timeout):
        """
        Run the event loop until timeout or explicit stop.

        Start the event loop running, and stop after approximately ``timeout``
        seconds, or when the ``stop`` method is called (whichever comes first).

        Parameters
        ----------
        timeout : float
            Maximum time to run the event loop for, in seconds.

        Returns
        -------
        stopped : bool
            ``True`` if the event loop was stopped as the resut of calling
            ``stop``, and ``False`` if it stopped as a result of timing out.
        """
        if self.state != IDLE:
            raise RuntimeError("Event loop is currently running")
        self.state = RUNNING
        stopped = self._run_until(lambda: self.state != RUNNING, timeout)
        self.state = IDLE
        return stopped

    def stop(self):
        """
        Stop a running event loop.

        Not thread safe. This should only be called from the main thread.
        """
        if self.state != RUNNING:
            raise RuntimeError("Can't stop an event loop that isn't running.")
        self.state = STOPPING

    def async_caller(self, event_handler):
        """
        Create an asynchronous version of a callable.

        Given a callable ``event_handler`` of a single argument,
        return another callable of a single argument that, when called,
        places an event on this event loops queue. When that event is
        eventually processed, ``event_handler`` will be called with
        the given arguments.

        Parameters
        ----------
        event_handler : callable of a single argument
            Callable to be executed asynchronously by the event loop.

        Returns
        -------
        async_event_handler : callable of a single argument
            Asynchronous version of ``event_handler``.
        """
        caller_id = next(self._caller_ids)
        self._event_handlers[caller_id] = event_handler
        return AsyncCaller(self._event_queue, caller_id)

    def run_until_no_handlers(self, timeout):
        """
        Run the event loop until all current event handlers have been closed.
        """
        return self._run_until(lambda: not self._event_handlers, timeout)

    # Private methods #########################################################

    def _run_until(self, condition, timeout):
        """
        Run the event loop until either a given condition holds, or timeout.

        The condition will be checked before processing each item from the
        event queue, and the loop will stop as soon as the condition becomes
        true, or until a given amount of time has passed without the condition
        becoming true.

        Note that the timeout is only approximate; in practice, the loop may
        run for slightly longer.

        Parameters
        ----------
        condition : callable
            This should be a callable accepting no arguments and returning
            a boolean.
        timeout : float
            Maximum time to run the event loop for, in seconds.
        """
        stop_time = time.time() + timeout
        while not condition():
            try:
                # This block effectively provides a version of Queue.get that
                # raises queue.Empty (not ValueError) for negative timeout.
                time_left = stop_time - time.time()
                if time_left <= 0.0:
                    raise queue.Empty
                else:
                    event = self._event_queue.get(timeout=time_left)
            except queue.Empty:
                # Timed out before the condition became true.
                return False

            # Python 2-compatible version of "action, *action_args = event".
            action_type, action_args = event[0], event[1:]

            if action_type == _CALL_ACTION:
                caller_id, args, kwargs = action_args
                event_handler = self._event_handlers[caller_id]
                event_handler(*args, **kwargs)
            else:  # action_type == CLOSE_ACTION
                assert action_type == _CLOSE_ACTION
                caller_id, = action_args
                self._event_handlers.pop(caller_id)

        # Condition became true.
        return True
