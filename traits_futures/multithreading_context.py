# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
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
from traits_futures.toolkit_support import toolkit


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
        event : event-like
            An event that can be shared safely with workers.
        """
        return threading.Event()

    def message_router(self):
        """
        Return a message router suitable for use in this context.

        Returns
        -------
        message_router : MessageRouter
        """
        router_class = toolkit("message_router:MessageRouter")
        return router_class()

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
