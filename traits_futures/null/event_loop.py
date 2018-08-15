"""
A bare bones event loop that doesn't need any UI framework.
"""

from __future__ import absolute_import, print_function, unicode_literals

import threading
import time

from six.moves import queue

from traits.api import Any, Event, HasStrictTraits, Unicode


class EventLoop(HasStrictTraits):
    """
    A simple event loop that doesn't require any UI framework.

    Events may be posted from any thread using the ``post_event`` method, and
    as each ``event`` is processed by the event loop the ``event`` trait will
    be fired.

    It's left to listeners to the ``event`` trait to filter the events
    intended for them and ignore the rest.
    """
    #: Event fired for each event put on the queue. Right now, all
    #: it carries is a string giving the event type.
    event = Event(Unicode)

    def start(self, timeout):
        """
        Start the event loop running, and stop after ``timeout``
        seconds or when the ``stop`` method is called.

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
            current_time = time.time()
            if current_time >= stop_time:
                break
            try:
                self.event = self._event_queue.get(
                    timeout=stop_time - current_time)
            except queue.Empty:
                break

        self._stop_event_loop = None
        return stop_event_loop.is_set()

    def stop(self):
        """
        Stop a running event loop.
        """
        self._stop_event_loop.set()

    def post_event(self, event):
        """
        Post an event to be processed by the event loop. Thread safe.

        This may be called at any time, regardless of whether the event
        loop is running or not.

        Parameters
        ----------
        event : string
            The type of the event to be processed.
        """
        self._event_queue.put(event)

    # Initialiser.

    def __init__(self, **traits):
        super(EventLoop, self).__init__(**traits)
        # Initialise the event queue non-lazily, because we want
        # to be sure that this happens in the main thread.
        self._event_queue = queue.Queue()

    # Private traits ##########################################################

    _event_queue = Any()

    _stop_event_loop = Any()


#: Global event loop.
_event_loop = None


def set_event_loop(event_loop):
    """
    Set the global event loop to the given one.
    """
    global _event_loop
    _event_loop = event_loop


def get_event_loop():
    """
    Get the current event loop. Raises RuntimeError if there is none.
    """
    if _event_loop is None:
        raise RuntimeError("No current event loop")
    return _event_loop


def clear_event_loop():
    """
    Clear the global event loop.
    """
    global _event_loop
    _event_loop = None
