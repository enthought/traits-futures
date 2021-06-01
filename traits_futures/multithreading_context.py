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

    Parameters
    ----------
    gui_context : IGuiContext
        GUI context to use for interactions with the GUI event loop.
    """

    def __init__(self, gui_context=None):
        assert gui_context is None
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

    def message_router(self, gui_context):
        """
        Return a message router suitable for use in this context.

        Parameters
        ----------
        gui_context : IGuiContext
            The GUI context providing the event loop to interact with.

        Returns
        -------
        message_router : MultithreadingRouter
        """
        return MultithreadingRouter(gui_context=gui_context)

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
