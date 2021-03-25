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
Tests for the MultiprocessingRouter class.
"""

import contextlib
import multiprocessing
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

from traits_futures.i_message_receiver import IMessageReceiver
from traits_futures.multiprocessing_router import MultiprocessingRouter
from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


#: Safety timeout, in seconds, for blocking operations, to prevent
#: the test suite from blocking indefinitely if something goes wrong.
SAFETY_TIMEOUT = 10.0


def send_messages(sender, messages):
    """
    Send the given messages using the given sender.
    """
    with sender:
        for message in messages:
            sender.send(message)


def send_without_starting(sender, messages):
    """
    Simluate a bad use of the sender.
    """
    for message in messages:
        sender.send(message)


class ReceiverListener(HasStrictTraits):
    """
    Test helper that listens to and records all messages from an
    IMessageReceiver.
    """

    #: The receiver that we're listening to.
    receiver = Instance(IMessageReceiver)

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


class TestMultiprocessingRouter(GuiTestAssistant, unittest.TestCase):
    """
    Tests that a MultiprocessingRouter presents the expected API
    and behaves as expected for multiprocessing background tasks.
    """

    router_factory = MultiprocessingRouter

    def setUp(self):
        GuiTestAssistant.setUp(self)

    def tearDown(self):
        GuiTestAssistant.tearDown(self)

    @contextlib.contextmanager
    def connected_router(self):
        """
        Return a context manager that yields an already connected router.

        Disconnects the router on leaving the associated with block.
        """
        router = self.router_factory()
        router.connect()
        try:
            yield router
        finally:
            router.disconnect()

    def test_pipe_without_connection(self):
        # Calling 'pipe' on an unstarted router should be an error.
        router = self.router_factory()

        with self.assertRaises(RuntimeError):
            router.pipe()

    def test_connect_twice(self):
        with self.connected_router() as router:
            with self.assertRaises(RuntimeError):
                router.connect()

    def test_no_thread_leaks(self):
        router = self.router_factory()

        threads_before = threading.enumerate()
        router.connect()
        router.disconnect()
        threads_after = threading.enumerate()

        self.assertEqual(len(threads_before), len(threads_after))

    def test_send_and_receive_messages(self):
        with self.connected_router() as router:
            sender, receiver = router.pipe()
            try:
                listener = ReceiverListener(receiver=receiver)

                messages = ["inconceivable", 15206, (23, 5.6)]

                worker = multiprocessing.Process(
                    target=send_messages,
                    args=(sender, messages),
                )

                worker.start()
                worker.join(timeout=SAFETY_TIMEOUT)
                # Fail if the join timed out, or if we got a nonzero exit code.
                self.assertEqual(worker.exitcode, 0)

                def got_all_messages(listener):
                    return len(listener.messages) >= len(messages)

                self.run_until(listener, "messages_items", got_all_messages)
            finally:
                router.close_pipe(receiver)

    def test_start_and_stop_in_main_thread(self):
        # It should also be safe to start, send and stop in the main thread
        # of the main process.
        with self.connected_router() as router:
            sender, receiver = router.pipe()
            try:
                listener = ReceiverListener(receiver=receiver)

                messages = ["inconceivable", 15206, (23, 5.6)]

                send_messages(sender, messages)

                def got_all_messages(listener):
                    return len(listener.messages) >= len(messages)

                self.run_until(listener, "messages_items", got_all_messages)
            finally:
                router.close_pipe(receiver)
