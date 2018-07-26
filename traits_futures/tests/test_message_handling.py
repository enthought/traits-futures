from __future__ import absolute_import, print_function, unicode_literals

import collections
import threading
import unittest

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant
from traits.api import HasStrictTraits, Instance, List, on_trait_change

from traits_futures.message_handling import QtMessageRouter

FINAL = "final"


def send_messages(sender, messages):
    """
    Send messages using a given sender.
    """
    with sender:
        for message in messages:
            sender.send(message)


class Listener(HasStrictTraits):
    # The router we're listening to.
    router = Instance(QtMessageRouter)

    # Messages received.
    messages = List

    @on_trait_change('router:received')
    def _record_message(self, message):
        self.messages.append(message)


class TestMessageHandling(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)

    def tearDown(self):
        GuiTestAssistant.tearDown(self)

    def test_message_sending_from_background_thread(self):
        # Sending from the same thread should work, and should
        # be synchronous: no need to run the event loop.
        router = QtMessageRouter()
        listener = Listener(router=router)
        sender_id, sender, _ = router.sender()

        messages = ["inconceivable", 15206, (23, 5.6), FINAL]

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

        expected_messages = [(sender_id, message) for message in messages]
        self.assertEqual(listener.messages, expected_messages)

    def test_multiple_senders(self):
        # Sending from the same thread should work, and should
        # be synchronous: no need to run the event loop.
        router = QtMessageRouter()
        listener = Listener(router=router)

        worker_count = 64

        sender_ids = []
        workers = []

        expected_messages = {}
        for i in range(worker_count):
            sender_id, sender, _ = router.sender()

            sender_ids.append(sender_id)

            messages = [i**2, FINAL]
            worker = threading.Thread(
                target=send_messages,
                args=(sender, messages),
            )
            workers.append(worker)
            expected_messages[sender_id] = messages

        # Run workers; wait until we receive the expected number of messages.
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()

        def received_all_messages():
            return len(listener.messages) >= 2 * worker_count

        with self.event_loop_until_condition(received_all_messages):
            pass

        # Sort messages by sender_id.
        received_messages = collections.defaultdict(list)
        for sender_id, message in listener.messages:
            received_messages[sender_id].append(message)

        self.assertEqual(received_messages, expected_messages)

    def test_synchronous_message_sending(self):
        # Sending from the same thread should work, and should
        # be synchronous: no need to run the event loop.
        router = QtMessageRouter()
        listener = Listener(router=router)
        sender_id, sender, _ = router.sender()

        messages = ["inconceivable", 15206, (23, 5.6), FINAL]
        with sender:
            for message in messages:
                sender.send(message)

        expected_messages = [(sender_id, message) for message in messages]
        self.assertEqual(listener.messages, expected_messages)
