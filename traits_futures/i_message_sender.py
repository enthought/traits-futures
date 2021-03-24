# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!


import abc
import contextlib

from traits.api import Interface


class IMessageSender(Interface, contextlib.AbstractContextManager):
    """
    Interface for objects used to send a message to the foreground.

    Typically an IMessageSender instance for a given router is created
    by that router.
    """

    @abc.abstractmethod
    def send(self, message):
        """
        Send a message to the router.

        Typically the message will be immutable, small, and pickleable.
        """
