# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

from traits.api import Any, Event, HasStrictTraits, Int, provides

from traits_futures.i_message_receiver import IMessageReceiver


@provides(IMessageReceiver)
class MessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from a sender.
    """

    #: Connection id, matching that of the paired sender.
    connection_id = Int()

    #: Event fired when a message is received from the paired sender.
    message = Event(Any())
