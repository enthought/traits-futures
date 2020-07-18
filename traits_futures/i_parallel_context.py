# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Interface for the parallelism context needed by the TraitsExecutor
"""

import abc


class IParallelContext(abc.ABC):
    """
    Interface for the parallelism context needed by the TraitsExecutor.

    A class implementing this interface provides a worker pool,
    message router and other concurrency primitives suitable for a
    particular form of parallelism, for example multithreading or
    multiprocessing.
    """

    @abc.abstractmethod
    def worker_pool(self, *, max_workers=None):
        """
        Provide a worker pool suitable for this context.

        Parameters
        ----------
        max_workers : int, optional
            Maximum number of workers in the worker pool. If not given, it's
            up to the worker pool to choose a suitable number of workers,
            perhaps dependent on the number of logical cores present on
            the target machine.

        Returns
        -------
        executor : concurrent.futures.Executor
        """

    @abc.abstractmethod
    def event(self):
        """
        Return a shareable event suitable for this context.

        Returns
        -------
        event : event-like
            An event that can be shared safely with workers.
            The event should have the same API as ``threading.Event``
            and ``multiprocessing.Event``, providing at a minimum
            the ``set`` and ``is_set`` methods from that API.
        """

    @abc.abstractmethod
    def queue(self):
        """
        Return a shareable queue suitable for this context.

        Returns
        -------
        queue : queue-like
            A queue that can be shared safely with workers. This package
            relies only on the ``put`` and ``get`` methods of the queue.
        """

    @abc.abstractmethod
    def message_router(self):
        """
        Return a message router suitable for use in this context.

        Returns
        -------
        message_router : MessageRouter
        """

    @abc.abstractmethod
    def close(self):
        """
        Do any cleanup necessary before disposal of the context.
        """

    @property
    @abc.abstractmethod
    def closed(self):
        """
        True if this context is closed, else False.
        """