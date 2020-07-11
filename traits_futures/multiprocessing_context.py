# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Context providing multiprocessing-friendly worker pools, events, and routers.
"""

import concurrent.futures
import multiprocessing

from traits_futures.i_parallel_context import IParallelContext
from traits_futures.toolkit_support import toolkit


class MultiprocessingContext(IParallelContext):
    def __init__(self):
        self._closed = False
        self._manager = multiprocessing.Manager()

    def worker_pool(self, *, max_workers=None):
        return concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)

    def event(self):
        return self._manager.Event()

    def queue(self):
        return self._manager.Queue()

    def message_router(self):
        MessageRouter = toolkit("message_process_router:MessageProcessRouter")
        return MessageRouter()

    def close(self):
        self._manager.shutdown()
        self._closed = True

    @property
    def closed(self):
        return self._closed
