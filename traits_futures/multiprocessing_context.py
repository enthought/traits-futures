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
Context providing multiprocessing-friendly worker pools, events, and routers.
"""

import concurrent.futures
import multiprocessing

from traits_futures.i_parallel_context import IParallelContext
from traits_futures.multiprocessing_router import MultiprocessingRouter


class MultiprocessingContext(IParallelContext):
    """
    Context for multiprocessing, suitable for use with the TraitsExecutor.

    Parameters
    ----------
    toolkit : Toolkit, optional
        Gui toolkit to use. If not given, the toolkit is determined based
        on what's available in the environment.
    """

    def __init__(self, toolkit):
        self._toolkit = toolkit
        self._closed = False
        self._manager = multiprocessing.Manager()

    def worker_pool(self, *, max_workers=None):
        """
        Provide a new worker pool suitable for this context.

        Parameters
        ----------
        max_workers : int, optional
            Maximum number of workers to use. If not given, the choice is
            delegated to the ProcessPoolExecutor.

        Returns
        -------
        executor : concurrent.futures.Executor
        """
        return concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)

    def event(self):
        """
        Return a shareable event suitable for this context.

        Returns
        -------
        event : event-like
            An event that can be shared safely with workers.
        """
        return self._manager.Event()

    def message_router(self):
        """
        Return a message router suitable for use in this context.

        Returns
        -------
        message_router : MultiprocessingRouter
        """
        return MultiprocessingRouter(
            manager=self._manager,
            _toolkit=self._toolkit,
        )

    def close(self):
        """
        Do any cleanup necessary before disposal of the context.
        """
        self._manager.shutdown()
        self._closed = True

    @property
    def closed(self):
        """
        True if this context is closed, else False.
        """
        return self._closed
