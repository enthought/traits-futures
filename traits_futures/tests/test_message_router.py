# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import threading
import unittest

from traits.api import (
    Any,
    Event,
    HasStrictTraits,
    Instance,
    List,
    on_trait_change,
)

from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


def send_messages(sender, messages):
    """
    Send messages using a given sender.
    """
    with sender:
        for message in messages:
            sender.send(message)


class ReceiverListener(HasStrictTraits):
    """
    Test helper that listens to and records all messages from a
    MessageReceiver.
    """

    #: The receiver that we're listening to.
    receiver = Any()

    #: Messages received.
    messages = List(Any())

    #: Event fired whenever a message arrives.
    message_received = Event()

    #: List of threads that messages arrived on.
    threads = List(Any)

    @on_trait_change("receiver:message")
    def _record_message(self, message):
        self.messages.append(message)
        self.threads.append(threading.current_thread())
        self.message_received = True


class MultiListener(HasStrictTraits):
    """
    Monitor a collection of listeners and fire an event whenever any
    one of them receives a message.
    """

    # Listeners we'll listen to.
    listeners = List(Instance(ReceiverListener))

    # Event fired whenever a message is received by any of the listeners.
    message_received = Event()

    @on_trait_change("listeners:message_received")
    def _fire_message_received(self):
        self.message_received = True


class TestMessageRouter(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.router = toolkit("message_router:MessageRouter")()
        self.router.connect()

    def tearDown(self):
        self.router.disconnect()
        del self.router
        GuiTestAssistant.tearDown(self)

    def test_message_sending_from_background_thread(self):
        sender, receiver = self.router.pipe()
        listener = ReceiverListener(receiver=receiver)

        messages = ["inconceivable", 15206, (23, 5.6)]

        # Send messages from a background thread.
        worker = threading.Thread(
            target=send_messages,
            args=(sender, messages),
        )
        worker.start()
        worker.join()

        def got_all_messages(listener):
            return len(listener.messages) >= len(messages)

        self.run_until(listener, "messages_items", got_all_messages)
        self.assertEqual(listener.messages, messages)

        # Check that all the messages arrived on the main thread
        # as expected.
        main_thread = threading.current_thread()
        for thread in listener.threads:
            self.assertEqual(thread, main_thread)

    def test_multiple_senders(self):
        worker_count = 64
        message_count = 64

        # Messages for each worker to send: one list of messages per worker.
        worker_messages = [
            [(i, j) for j in range(message_count)] for i in range(worker_count)
        ]

        workers = []
        listeners = []
        for messages in worker_messages:
            sender, receiver = self.router.pipe()
            listeners.append(ReceiverListener(receiver=receiver))
            workers.append(
                threading.Thread(
                    target=send_messages,
                    args=(sender, messages),
                )
            )

        monitor = MultiListener(listeners=listeners)

        # Run the workers.
        for worker in workers:
            worker.start()

        # Wait until we receive the expected number of messages.
        def received_all_messages(monitor):
            return all(
                len(listener.messages) >= message_count
                for listener in monitor.listeners
            )

        self.run_until(monitor, "message_received", received_all_messages)

        # Workers should all be ready to join.
        for worker in workers:
            worker.join()

        # Check we got the expected messages.
        received_messages = [listener.messages for listener in listeners]
        self.assertEqual(received_messages, worker_messages)
