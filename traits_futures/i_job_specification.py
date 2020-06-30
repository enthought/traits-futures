# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Interface for a job specification. The job specification is the object
that the TraitsExecutor knows how to deal with.
"""

from abc import ABC, abstractmethod


class IJobSpecification(ABC):
    @abstractmethod
    def background_job(self):
        """
        Return the callable that will be invoked as the background job.

        This callable should be pickleable, should have the signature

            job(send, cancelled)

        Any return value from the callable will be ignored.

        The ``send`` argument can be used by the background job to send
        messages back to the main thread of execution. It's a callable that can
        be used either in the form ``send(message_type)`` or in the form
        ``send(message_type, message_args)``. Here ``message_type`` is a simple
        constant (typically a string), and ``message_args`` is a single Python
        object containing optional arguments for the message. The arguments to
        ``send`` should typically be both immutable and pickleable. ``send``
        returns no useful result.

        The ``cancelled`` argument may be used by the background job to check
        whether cancellation has been requested. It returns either ``True``
        to indicate that cancellation has been requested, or ``False``.

        Note that there's no obligation for the background job to check the
        cancellation status.

        Returns
        -------
        job : callable
        """

    @abstractmethod
    def future(self, cancel, message_receiver):
        """
        Return a Future for the background job.

        Parameters
        ----------
        cancel : callable
            Zero-argument callable that can be called to request cancellation
            of the background task.
        receiver : IMessageReceiver
            HasTraits instance with a ``message`` trait, which can be listened
            to in order to receive messages from the background job.

        Returns
        -------
        future : IFuture
            Future object that can be used to monitor the status of the
            background job.
        """
