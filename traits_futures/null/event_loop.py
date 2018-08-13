from __future__ import absolute_import, print_function, unicode_literals

import threading

from six.moves import queue

from traits.api import Any, Event, HasStrictTraits, Unicode


class EventLoop(HasStrictTraits):
    #: Event fired for each message put on the queue. Right now, all
    #: it carries is a string message type.
    message = Event(Unicode)

    _message_queue = Any()

    _stop_event = Any()

    def __init__(self):
        self._message_queue = queue.Queue()

    def run(self):
        self._stop_event = stop_event = threading.Event()
        while not stop_event.is_set():
            self.message = self._message_queue.get()
        self._stop_event = None

    def stop(self):
        """
        Stop the event loop from running.
        """
        self._stop_event.set()

    def post_message(self, message):
        """
        Post a message. Thread safe.
        """
        # Assumes that self.message_queue is never removed.
        self._message_queue.put(message)


#: Global event loop.
_event_loop = None

def set_event_loop(event_loop):
    global _event_loop
    _event_loop = event_loop

def get_event_loop():
    if _event_loop is None:
        raise RuntimeError("No current event loop")
    return _event_loop

def clear_event_loop():
    global _event_loop
    _event_loop = None
