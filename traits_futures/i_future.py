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
Interface for futures returned by the executor.
"""

import abc


class IFuture(abc.ABC):
    """
    Interface for futures returned by the executor.

    This interface can be used to implement new
    background task types. It represents the knowledge that the executor needs
    to interact with futures.
    """

    @abc.abstractmethod
    def cancel(self):
        """
        Request cancellation of the background task.

        For a future that has not yet completed and has not previously been
        cancelled, this method requests cancellation of the associated
        background task and returns ``True``. For a future that has already
        completed, or that has previously been cancelled, this method
        does nothing, and returns ``False``.

        Returns
        -------
        cancelled : bool
            True if the task was cancellable and this call requested
            cancellation, False if the task was not cancellable (in which case
            this call did nothing).
        """

    @abc.abstractmethod
    def receive(self, message):
        """
        Receive and process a message from the task associated to this future.

        This method is primarily for use by the executors, but may also be of
        use in testing.

        Parameters
        ----------
        message : object
            The message received from the associated task.

        Returns
        -------
        final : bool
            True if the received message should be the last one ever received
            from the paired task.
        """
