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
Interface for a job specification. The job specification is the object
that the TraitsExecutor knows how to deal with.
"""

from abc import ABC, abstractmethod


class ITaskSpecification(ABC):
    """
    Specify background task callable and foreground future for a task.

    An object implementing the ITaskSpecification interface describes how to
    create a background task and a corresponding foreground future to execute a
    particular type of background task. It's consumed by the TraitsExecutor
    when submitting background tasks, and implemented by BackgroundCall,
    BackgroundIteration and others.
    """

    @abstractmethod
    def task(self):
        """
        Return the callable that will be invoked as the background task.

        This callable should be pickleable and should have the signature

            task(send, cancelled)

        Any exception raised while executing the callable, or result returned
        by the callable, will be recorded in the corresponding future.

        The ``send`` argument can be used by the background task to send
        messages back to the main thread of execution. It's a callable that
        should be called as ``send(message)``, where ``message`` is an
        arbitrary Python object. The argument to ``send`` should typically be
        both immutable and pickleable. ``send`` returns no useful result.

        The ``cancelled`` argument may be used by the background task to check
        whether cancellation has been requested. When called with no arguments,
        it returns either ``True`` to indicate that cancellation has been
        requested, or ``False``.

        Note that there's no obligation for the background task to check the
        cancellation status.

        Returns
        -------
        task : object
            Callable accepting arguments ``send`` and ``cancelled``. The
            callable can use ``send`` to send messages and ``cancelled`` to
            check whether cancellation has been requested.
        """

    @abstractmethod
    def future(self, cancel):
        """
        Return a Future for the background task.

        Parameters
        ----------
        cancel
            Zero-argument callable, returning no useful result. The returned
            future's ``cancel`` method should call this to request cancellation
            of the associated background task.

        Returns
        -------
        future : IFuture
            Future object that can be used to monitor the status of the
            background task.
        """
