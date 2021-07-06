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
Common tests for testing implementations of the IMessageRouter interface.
"""

import contextlib
import logging
import threading

from traits.api import Any, HasStrictTraits, Instance, List, observe, Str

from traits_futures.i_message_router import IMessageReceiver
from traits_futures.i_parallel_context import IParallelContext

#: Safety timeout, in seconds, for blocking operations, to prevent
#: the test suite from blocking indefinitely if something goes wrong.
SAFETY_TIMEOUT = 10.0


def send_messages(sender, messages):
    """
    Send a sequence of messages using the given sender.

    Parameters
    ----------
    sender : IMessageSender
        The sender to use to send messages.
    messages : list
        List of objects to send.
    """
    sender.start()
    try:
        for message in messages:
            sender.send(message)
    finally:
        sender.stop()


class ReceiverListener(HasStrictTraits):
    """
    Listener for a receiver, recording received messages.
    """

    #: The receiver that we're listening to.
    receiver = Instance(IMessageReceiver)

    #: Received messages
    messages = List(Any())

    @observe("receiver:message")
    def _record_message(self, event):
        message = event.new
        self.messages.append(message)


class CapturingHandler(logging.Handler):
    """
    Logging handler capturing raw and formatted logging output.

    Adapted from unittest._log in the standard library.
    """

    def __init__(self):
        logging.Handler.__init__(self)
        self.watcher = LoggingWatcher()

    def flush(self):
        pass

    def emit(self, record):
        self.watcher.records.append(record)
        msg = self.format(record)
        self.watcher.output.append(msg)


class LoggingWatcher(HasStrictTraits):
    """
    Traited logging watcher that records raw records and formatted messages.
    """

    #: Logged records.
    records = List(Instance(logging.LogRecord))

    #: Formatted logged meesages.
    output = List(Str())


class IMessageRouterTests:
    """
    Test mix-in for testing implementations of the IMessageRouter interface.

    Should be used in conjunction with the GuiTestAssistant.
    """

    #: Factory providing the parallelism context.
    # Override this in implementations. It should be a zero-argument
    # callable that produces the appropriate IParallelContext instance
    # when called.
    context_factory = IParallelContext

    def setUp(self):
        self.context = self.context_factory()

    def tearDown(self):
        self.context.close()
        del self.context

    def test_send_and_receive(self):
        with self.context.worker_pool() as worker_pool:
            with self.started_router() as router:
                # Given
                sender, receiver = router.pipe()
                listener = ReceiverListener(receiver=receiver)
                messages = ["Just testing", 314]

                # When
                worker_pool.submit(send_messages, sender, messages)

                # Then
                self.assertEventuallyReceives(listener, messages)

                # Clean up
                router.close_pipe(receiver)

    def test_send_and_receive_multiple_senders(self):
        # Variant of test_send_and_receive for multiple independent
        # message streams.

        # Labels used to identify tasks.
        tasks = range(64)

        with self.context.worker_pool() as worker_pool:
            with self.started_router() as router:
                # Senders, receivers, listeners and messages, keyed by task.
                sender, receiver, listener, messages = {}, {}, {}, {}

                # Create one pipe per task.
                for task in tasks:
                    sender[task], receiver[task] = router.pipe()
                    listener[task] = ReceiverListener(receiver=receiver[task])
                    messages[task] = [(task, message) for message in range(64)]

                # Start the jobs
                for task in tasks:
                    worker_pool.submit(
                        send_messages, sender[task], messages[task]
                    )

                # Check the results.
                for task in tasks:
                    self.assertEventuallyReceives(
                        listener[task], messages[task]
                    )

                # Clean up.
                for task in tasks:
                    router.close_pipe(receiver[task])

    def test_send_and_receive_main_thread(self):
        # Variant of send_and_receive where we send on the main thread,
        # without using a worker. This should still work.
        with self.started_router() as router:
            # Given
            sender, receiver = router.pipe()
            listener = ReceiverListener(receiver=receiver)
            messages = ["Just testing", 314]

            # When
            send_messages(sender, messages)

            # Then
            self.assertEventuallyReceives(listener, messages)

            # Cleanup
            router.close_pipe(receiver)

    def test_start_already_started_router(self):
        with self.started_router() as router:
            with self.assertRaises(RuntimeError):
                router.start()

    def test_stop_unstarted_router(self):
        router = self.context.message_router(event_loop=self._event_loop)
        with self.assertRaises(RuntimeError):
            router.stop()

    def test_pipe_for_unstarted_router(self):
        router = self.context.message_router(event_loop=self._event_loop)
        with self.assertRaises(RuntimeError):
            router.pipe()

    def test_pipe_for_stopped_router(self):
        with self.started_router() as router:
            pass
        with self.assertRaises(RuntimeError):
            router.pipe()

    def test_close_pipe_for_stopped_router(self):
        with self.assertLogs("traits_futures", level="WARNING"):
            with self.started_router() as router:
                _, receiver = router.pipe()

        with self.assertRaises(RuntimeError):
            router.close_pipe(receiver)

    def test_unclosed_pipe(self):
        # Stopping the router with unclosed pipes
        with self.assertLogs("traits_futures", level="WARNING") as cm:
            with self.started_router() as router:
                router.pipe()

        all_log_messages = "\n".join(cm.output)
        self.assertIn("unclosed pipes", all_log_messages)

    def test_threads_cleaned_up(self):
        threads_before = threading.enumerate()
        with self.started_router():
            pass
        threads_after = threading.enumerate()
        self.assertEqual(len(threads_after), len(threads_before))

    def test_send_after_close(self):
        with self.started_router() as router:
            sender, receiver = router.pipe()
            router.close_pipe(receiver)

            # There should be no problem with sending. But eventually the
            # router will receive the message and fail to find a receiver.
            # At that point it should log.
            with self.assertEventuallyLogs(
                "traits_futures", level="WARNING"
            ) as cm:
                sender.start()
                sender.send("some message")
                sender.stop()

            all_log_messages = "\n".join(cm.output)
            self.assertIn(
                "discarding message from closed pipe", all_log_messages
            )

    def test_sender_send_without_start(self):
        with self.started_router() as router:
            with self.get_sender(router) as sender:
                with self.assertRaises(RuntimeError):
                    sender.send("Some message")

    def test_sender_start_twice(self):
        with self.started_router() as router:
            with self.get_sender(router) as sender:
                sender.start()
                with self.assertRaises(RuntimeError):
                    sender.start()
                sender.stop()

    def test_sender_stop_before_start(self):
        with self.started_router() as router:
            with self.get_sender(router) as sender:
                with self.assertRaises(RuntimeError):
                    sender.stop()

    def test_sender_stop_twice(self):
        with self.started_router() as router:
            with self.get_sender(router) as sender:
                sender.start()
                sender.stop()
                with self.assertRaises(RuntimeError):
                    sender.stop()

    def test_sender_restart(self):
        with self.started_router() as router:
            with self.get_sender(router) as sender:
                sender.start()
                sender.stop()
                with self.assertRaises(RuntimeError):
                    sender.start()

    # Helper functions and assertions

    @contextlib.contextmanager
    def get_sender(self, router):
        """
        Provide a sender for the given router, and do cleanup afterwards.
        """
        sender, receiver = router.pipe()
        try:
            yield sender
        finally:
            router.close_pipe(receiver)

    @contextlib.contextmanager
    def started_router(self):
        """
        A context manager that yields an already-started router.

        Stops the router on context manager exit.
        """
        router = self.context.message_router(event_loop=self._event_loop)
        router.start()
        try:
            yield router
        finally:
            router.stop()

    def assertEventuallyReceives(
        self, listener, messages, *, timeout=SAFETY_TIMEOUT
    ):
        """
        Assert that a given listener eventually receives the given messages.

        Runs the event loop until either the expected messages are received,
        or until timeout.

        Parameters
        ----------
        listener : ReceiverListener
        messages : list
            List of messages that are expected.
        timeout : float
            Maximum time to wait for the messages to arrive, in seconds.
        """

        def got_enough_messages(listener):
            return len(listener.messages) >= len(messages)

        self.run_until(
            object=listener,
            trait="messages_items",
            condition=got_enough_messages,
            timeout=timeout,
        )
        self.assertEqual(listener.messages, messages)

    @contextlib.contextmanager
    def assertEventuallyLogs(
        self, logger=None, level=logging.INFO, *, timeout=SAFETY_TIMEOUT
    ):
        """
        Assert that we eventually get a log message matching the given pattern.

        Runs the event loop until either the expected log message is received,
        or until timeout. The API roughly matches that of the standard library
        assertLogs method, and much of the code is shamelessly adapted from
        the assertLogs source.
        """

        # Turn a logger name into the corresponding logger.
        if not isinstance(logger, logging.Logger):
            logger = logging.getLogger(logger)

        formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
        handler = CapturingHandler()
        handler.setFormatter(formatter)
        watcher = handler.watcher

        old_handlers = logger.handlers[:]
        old_level = logger.level
        old_propagate = logger.propagate

        logger.handlers = [handler]
        logger.setLevel(level)
        logger.propagate = False

        try:
            yield watcher
            self.run_until(
                object=watcher,
                trait="records_items",
                condition=lambda watcher: len(watcher.records) > 0,
                timeout=timeout,
            )
        finally:
            logger.handlers = old_handlers
            logger.propagate = old_propagate
            logger.setLevel(old_level)
