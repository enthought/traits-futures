"""
A bare-bones event loop that doesn't need any UI framework.
"""

from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools
import threading
import time

from six.moves import queue

from traits.api import (
    Any, Dict, HasStrictTraits, HasTraits, Instance, Int, Str, Tuple,
)


class EventPoster(object):
    """
    Object allowing posting of events of a given event type.
    """
    def __init__(self, event_queue, event_type):
        self._event_queue = event_queue
        self._event_type = event_type

    def post_event(self, event_args):
        """
        Post an event to the event queue.

        This method is thread-safe.
        """
        self._event_queue.put((self._event_type, event_args))


class EventLoop(HasStrictTraits):
    """
    A simple Traits-based event loop that doesn't require any UI framework.
    """
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
            time_left = stop_time - time.time()
            if time_left <= 0.0:
                break

            try:
                event_type, event_args = self._event_queue.get(
                    timeout=time_left)
            except queue.Empty:
                break

            object, event_name = self._event_receivers[event_type]
            setattr(object, event_name, event_args)

        self._stop_event_loop = None
        return stop_event_loop.is_set()

    def stop(self):
        """
        Stop a running event loop.

        Not thread safe. This should only be called from the main thread.
        """
        self._stop_event_loop.set()

    def event_poster(self, object, event_name):
        """
        Create a new event type and a poster object for that event.

        Creates a new event type, and returns a poster for that event.
        Whenever the event is processed, the given Event trait on the given
        object will be fired.
        """
        event_type = next(self._event_types)
        poster = EventPoster(self._event_queue, event_type)
        self._event_receivers[event_type] = object, event_name
        return poster

    def disconnect(self, event_poster):
        """
        Disconnect the given event poster from the event loop.

        Events posted using the event poster will no longer be handled by
        the event loop.
        """
        event_type = event_poster._event_type
        del self._event_receivers[event_type]

    # Initialiser.

    def __init__(self, **traits):
        super(EventLoop, self).__init__(**traits)
        # Initialise the event queue non-lazily, because we want
        # to be sure that this happens in the main thread.
        self._event_queue = queue.Queue()

    # Private traits ##########################################################

    #: Events waiting to be processed.
    _event_queue = Instance(queue.Queue)

    #: Registered receivers.
    _event_receivers = Dict(Int(), Tuple(Instance(HasTraits), Str))

    #: Source of event types.
    _event_types = Instance(collections.Iterator)

    #: Event used to indicate that the event loop should be stopped.
    _stop_event_loop = Any()

    # Private methods #########################################################

    def __event_types_default(self):
        return itertools.count()


#: Global event loop.
_event_loop = None


def get_event_loop():
    """
    Get the current event loop. Raises RuntimeError if there is none.
    """
    if _event_loop is None:
        raise RuntimeError("No current event loop")
    return _event_loop


def set_event_loop(event_loop):
    """
    Set the global event loop to the given one.
    """
    global _event_loop
    _event_loop = event_loop


def clear_event_loop():
    """
    Clear the global event loop.
    """
    global _event_loop
    _event_loop = None
