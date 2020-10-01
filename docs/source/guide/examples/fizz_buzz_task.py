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
Example of a user-created background task type.
"""

# This Python file provides supporting code for the "advanced" section of the
# user guide. Because we're using pieces of the file for documentation
# snippets, the overall structure of this file is a little odd, and doesn't
# follow standard style guidelines (for example, placing imports at the top
# of the file). The various '# -- start' and '# -- end' markers are there
# to allow the documentation build to extract the appropriate pieces.


# -- start message types
FIZZ = "fizz"
BUZZ = "buzz"
FIZZ_BUZZ = "fizz_buzz"
# -- end message types


# -- start fizz_buzz --
import time


def fizz_buzz(send, cancelled):
    """
    Count slowly from 1, sending FIZZ / BUZZ messages to the foreground.

    Parameters
    ----------
    send : callable(message_type, message_argument) -> None
        Callable accepting two arguments: a message type (a string) as the
        first argument, and the message argument (if any) as the optional
        second argument. The message argument should be pickleable, and
        preferably immutable (or at least, not intended to be mutated). It
        should return nothing.
    cancelled : callable
        Callable accepting no arguments and returning a boolean result. It
        returns ``True`` if cancellation has been requested, and ``False``
        otherwise.
    """
    n = 1
    while not cancelled():

        n_is_multiple_of_3 = n % 3 == 0
        n_is_multiple_of_5 = n % 5 == 0

        if n_is_multiple_of_3 and n_is_multiple_of_5:
            send(FIZZ_BUZZ, n)
        elif n_is_multiple_of_3:
            send(FIZZ, n)
        elif n_is_multiple_of_5:
            send(BUZZ, n)

        time.sleep(1.0)
        n += 1
# -- end fizz_buzz --


# -- start FizzBuzzFuture --
from traits.api import Event, Int
from traits_futures.api import BaseFuture


class FizzBuzzFuture(BaseFuture):
    """
    Object representing the front-end handle to a running fizz_buzz call.
    """

    #: Event fired whenever we get a FIZZ message. The payload is the
    #: corresponding integer.
    fizz = Event(Int)

    #: Event fired whenever we get a BUZZ message. The payload is the
    #: corresponding integer.
    buzz = Event(Int)

    #: Event fired whenever a FIZZ_BUZZ arrives from the background.
    #: The payload is the corresponding integer.
    fizz_buzz = Event(Int)

    # Private methods #########################################################

    def _process_fizz(self, n):
        self.fizz = n

    def _process_buzz(self, n):
        self.buzz = n

    def _process_fizz_buzz(self, n):
        self.fizz_buzz = n
# -- end FizzBuzzFuture --


# -- start BackgroundFizzBuzz --
from traits_futures.api import ITaskSpecification


@ITaskSpecification.register
class BackgroundFizzBuzz:
    """
    Task specification for Fizz Buzz background tasks.
    """

    def future(self):
        """
        Return a Future for the background task.

        Returns
        -------
        FizzBuzzFuture
            Future object that can be used to monitor the status of the
            background task.
        """
        return FizzBuzzFuture()

    def background_task(self):
        """
        Return a background callable for this task specification.

        Returns
        -------
        collections.abc.Callable
            Callable accepting arguments ``send`` and ``cancelled``. The
            callable can use ``send`` to send messages and ``cancelled`` to
            check whether cancellation has been requested.
        """
        return fizz_buzz
# -- end BackgroundFizzBuzz


# -- start submit_fizz_buzz
def submit_fizz_buzz(executor):
    """
    Convenience function to submit a Fizz buzz task to an executor.

    Parameters
    ----------
    executor : TraitsExecutor
        The executor to submit the task to.

    Returns
    -------
    future : FizzBuzzFuture
        The future for the background task, allowing monitoring and
        cancellation of the background task.
    """
    task = BackgroundFizzBuzz()
    future = executor.submit(task)
    return future
# -- end submit_fizz_buzz
