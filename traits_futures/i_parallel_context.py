# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Interface for the parallelism context needed by the TraitsExecutor
"""

from abc import ABC, abstractmethod


class IParallelContext(ABC):
    """
    Interface for the parallelism context needed by the TraitsExecutor.

    A class implementing this interface provides a worker pool,
    message router and other concurrency primitives suitable for a
    particular form of parallelism, for example multithreading or
    multiprocessing.
    """

    @abstractmethod
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

    @abstractmethod
    def event(self):
        """
        Return a shareable event suitable for this context.

        Returns
        -------
        event : event-like
            An event that can be shared safely with workers.
        """

    @abstractmethod
    def queue(self):
        """
        Return a shareable queue suitable for this context.

        Returns
        -------
        queue : queue-like
            A queue that can be shared safely with workers.
        """

    @abstractmethod
    def message_router(self):
        """
        Return a message router suitable for use in this context.

        Returns
        -------
        message_router : MessageRouter
        """

    @abstractmethod
    def close(self):
        """
        Do any cleanup necessary before disposal of the context.
        """

    @property
    @abstractmethod
    def closed(self):
        """
        True if this context is closed, else False.
        """
