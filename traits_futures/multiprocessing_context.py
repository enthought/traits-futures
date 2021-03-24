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
        return MultiprocessingRouter()

    def close(self):
        self._manager.shutdown()
        self._closed = True

    @property
    def closed(self):
        return self._closed
