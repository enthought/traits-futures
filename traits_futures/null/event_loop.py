"""
A bare-bones event loop that doesn't need any UI framework.
"""

from __future__ import absolute_import, print_function, unicode_literals

import itertools
import threading
import time

from six.moves import queue


class AsyncCaller(object):
    """
    Object allowing asynchronous execution of a callable.

    This object may be shared across threads.
    """
    def __init__(self, event_queue, event_type):
        self._event_queue = event_queue
        self._event_type = event_type

    def __call__(self, event_args):
        """
        Request the event loop to call with the given argument.

        This posts an event to the event queue; when that event is processed,
        the linked callable will be called with the given arguments.

        This method is thread-safe.
        """
        self._event_queue.put((self._event_type, event_args))


class EventLoop(object):
    """
    A simple event loop that doesn't require any UI framework.

    This event loop has exactly one trick, and that's the ability
    to fire callables asynchronously.
    """
    def __init__(self):
        self._event_queue = queue.Queue()
        self._event_receivers = {}
        self._event_types = itertools.count()
        self._stop_event_loop = None

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
        self._stop_event_loop = stop_event_loop = threading.Event()
        stop_time = time.time() + timeout

        while not stop_event_loop.is_set():
            time_left = stop_time - time.time()
            if time_left <= 0.0:
                break

            try:
                event_type, event_args = self._event_queue.get(
                    timeout=time_left)
            except queue.Empty:
                break

            event_handler = self._event_receivers[event_type]
            event_handler(event_args)

        self._stop_event_loop = None
        return stop_event_loop.is_set()

    def stop(self):
        """
        Stop a running event loop.

        Not thread safe. This should only be called from the main thread.
        """
        self._stop_event_loop.set()

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
        event_type = next(self._event_types)
        self._event_receivers[event_type] = event_handler
        return AsyncCaller(self._event_queue, event_type)

    def disconnect(self, async_caller):
        """
        Disconnect the given caller from the event loop.

        After this, it will no longer be possible to use this caller.
        """
        event_type = async_caller._event_type
        del self._event_receivers[event_type]


#: Global event loop.
_event_loop = None


def get_event_loop():
    """
    Get the current event loop. Returns ``None`` if there isn't one.
    """
    return _event_loop


def set_event_loop(event_loop):
    """
    Set the global event loop to the given one.

    Can be called with ``None`` to clear the current event loop.
    """
    global _event_loop
    _event_loop = event_loop
