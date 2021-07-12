# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Context providing multithreading-friendly worker pools, events, and routers.
"""

import concurrent.futures
import threading

from traits_futures.i_parallel_context import IParallelContext
from traits_futures.multithreading_router import MultithreadingRouter


class MultithreadingContext(IParallelContext):
    """
    Context for multithreading, suitable for use with the TraitsExecutor.
    """

    def __init__(self):
        self._closed = False

    def worker_pool(self, *, max_workers=None):
        """
        Provide a new worker pool suitable for this context.

        Parameters
        ----------
        max_workers : int, optional
            Maximum number of workers to use. If not given, the choice is
            delegated to the ThreadPoolExecutor.

        Returns
        -------
        executor : concurrent.futures.Executor
        """
        return concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def event(self):
        """
        Return a shareable event suitable for this context.

        Returns
        -------
        event : object
            An event that can be shared safely with workers.
            The event should have the same API as ``threading.Event``
            and ``multiprocessing.Event``, providing at a minimum
            the ``set`` and ``is_set`` methods from that API.
        """
        return threading.Event()

    def message_router(self, event_loop):
        """
        Return a message router suitable for use in this context.

        Parameters
        ----------
        event_loop : IEventLoop
            The event loop used to trigger message dispatch.

        Returns
        -------
        message_router : MultithreadingRouter
        """
        return MultithreadingRouter(event_loop=event_loop)

    def close(self):
        """
        Do any cleanup necessary before disposal of the context.
        """
        self._closed = True

    @property
    def closed(self):
        """
        True if this context is closed, else False.
        """
        return self._closed
