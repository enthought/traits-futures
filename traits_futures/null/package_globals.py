"""
Global shared state for this package.
"""
from __future__ import absolute_import, print_function, unicode_literals

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
