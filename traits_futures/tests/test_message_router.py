from __future__ import absolute_import, print_function, unicode_literals

import threading
import unittest

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant
from traits.api import Any, HasStrictTraits, Instance, List, on_trait_change

from traits_futures.qt.message_router import (
    MessageReceiver,
    MessageRouter,
)


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
    receiver = Instance(MessageReceiver)

    #: Messages received.
    messages = List(Any())

    #: List of threads that messages arrived on.
    threads = List(Any)

    @on_trait_change('receiver:message')
    def _record_message(self, message):
        self.messages.append(message)
        self.threads.append(threading.current_thread())


class TestMessageRouter(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)

    def tearDown(self):
        GuiTestAssistant.tearDown(self)

    def test_message_sending_from_background_thread(self):
        # Sending from the same thread should work, and should
        # be synchronous: no need to run the event loop.
        router = MessageRouter()
        sender, receiver = router.pipe()
        listener = ReceiverListener(receiver=receiver)

        messages = ["inconceivable", 15206, (23, 5.6)]

        # Send messages from a background thread.
        worker = threading.Thread(
            target=send_messages,
            args=(sender, messages),
        )
        worker.start()
        worker.join()

        def got_all_messages():
            return len(listener.messages) >= len(messages)

        with self.event_loop_until_condition(got_all_messages):
            pass

        self.assertEqual(listener.messages, messages)

        # Check that all the messages arrived on the main thread
        # as expected.
        main_thread = threading.current_thread()
        for thread in listener.threads:
            self.assertEqual(thread, main_thread)

    def test_multiple_senders(self):
        # Sending from the same thread should work, and should
        # be synchronous: no need to run the event loop.
        router = MessageRouter()
        worker_count = 64
        message_count = 64

        # Messages for each worker to send: one list of messages per worker.
        worker_messages = [
            [(i, j) for j in range(message_count)]
            for i in range(worker_count)
        ]

        workers = []
        listeners = []
        for messages in worker_messages:
            sender, receiver = router.pipe()
            listeners.append(ReceiverListener(receiver=receiver))
            workers.append(
                threading.Thread(
                    target=send_messages,
                    args=(sender, messages),
                )
            )

        # Run the workers.
        for worker in workers:
            worker.start()

        # Wait until we receive the expected number of messages.
        def received_all_messages():
            return all(
                len(listener.messages) >= message_count
                for listener in listeners
            )

        with self.event_loop_until_condition(received_all_messages):
            pass

        # Workers should all be ready to join.
        for worker in workers:
            worker.join()

        # Check we got the expected messages.
        received_messages = [listener.messages for listener in listeners]
        self.assertEqual(received_messages, worker_messages)
