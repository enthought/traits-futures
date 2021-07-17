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
import time

from traits.api import Any, HasStrictTraits, Instance, List, observe, Str

from traits_futures.i_message_router import IMessageReceiver
from traits_futures.i_parallel_context import IParallelContext

#: Safety timeout, in seconds, for blocking operations, to prevent
#: the test suite from blocking indefinitely if something goes wrong.
SAFETY_TIMEOUT = 10.0


def send_messages(sender, messages, message_delay=None):
    """
    Send a sequence of messages using the given sender.

    Parameters
    ----------
    sender : IMessageSender
        The sender to use to send messages.
    messages : list
        List of objects to send.
    message_delay : float, optional
        If given, the time to sleep before sending each message.
    """
    sender.start()
    try:
        for message in messages:
            if message_delay is not None:
                time.sleep(message_delay)
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

    Should be used in conjunction with the TestAssistant.
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

    def test_route_until(self):
        # When we've sent messages (e.g., from a background thread), we can
        # drive the router manually to receive those messages.

        messages = ["abc", "def"]

        with self.context.worker_pool() as worker_pool:
            with self.started_router() as router:
                sender, receiver = router.pipe()
                try:
                    listener = ReceiverListener(receiver=receiver)
                    worker_pool.submit(send_messages, sender, messages)
                    router.route_until(
                        lambda: len(listener.messages) >= len(messages),
                        timeout=SAFETY_TIMEOUT,
                    )
                finally:
                    router.close_pipe(receiver)

        self.assertEqual(listener.messages, messages)

    def test_route_until_without_timeout(self):
        # This test is mildly dangerous: if something goes wrong, it could
        # hang indefinitely. xref: enthought/traits-futures#310

        messages = ["abc"]

        with self.context.worker_pool() as worker_pool:
            with self.started_router() as router:
                sender, receiver = router.pipe()
                try:
                    listener = ReceiverListener(receiver=receiver)

                    worker_pool.submit(send_messages, sender, messages)

                    router.route_until(
                        lambda: len(listener.messages) >= len(messages),
                    )
                finally:
                    router.close_pipe(receiver)

        self.assertEqual(listener.messages, messages)

    def test_route_until_timeout(self):
        with self.started_router() as router:
            start_time = time.monotonic()
            with self.assertRaises(RuntimeError):
                router.route_until(lambda: False, timeout=0.1)
            actual_timeout = time.monotonic() - start_time

        self.assertLess(actual_timeout, 1.0)

    def test_route_until_timeout_with_repeated_messages(self):
        # Check for one plausible variety of implementation bug: re-using
        # the original timeout on each message get operation instead of
        # re-calculating the time to wait.
        with self.context.worker_pool() as worker_pool:
            with self.started_router() as router:
                sender, receiver = router.pipe()
                try:
                    listener = ReceiverListener(receiver=receiver)

                    # Send one seconds' worth of messages, but timeout after
                    # 0.1 seconds.
                    worker_pool.submit(
                        send_messages, sender, range(20), message_delay=0.05
                    )
                    with self.assertRaises(RuntimeError):
                        router.route_until(lambda: False, timeout=0.1)
                finally:
                    router.close_pipe(receiver)

        # With a timeout of 0.1 and only one message sent every 0.05 seconds,
        # we should have got at most 2 messages before timeout. To avoid
        # spurious failures due to timing variations, we allow up to 4.
        self.assertLessEqual(len(listener.messages), 4)

    def test_route_until_second_call_after_timeout(self):
        with self.started_router() as router:
            with self.assertRaises(RuntimeError):
                router.route_until(lambda: False, timeout=0.1)
            # Just check that the first call hasn't put the router into
            # an unusable state.
            router.route_until(lambda: True, timeout=SAFETY_TIMEOUT)

    def test_route_until_timeout_with_queued_messages(self):
        # Even with a timeout of 0.0, route_until shouldn't fail if
        # there are sufficient messages already queued to satisfy
        # the condition.
        messages = list(range(10))

        with self.started_router() as router:
            sender, receiver = router.pipe()
            listener = ReceiverListener(receiver=receiver)
            try:
                with self.context.worker_pool() as worker_pool:
                    worker_pool.submit(send_messages, sender, messages)

                # At this point we've closed the worker pool, so all
                # background jobs have completed and all messages are
                # already queued. route_until should be able to
                # process all of them, regardless of timeout.
                router.route_until(
                    lambda: len(listener.messages) >= len(messages),
                    timeout=0.0,
                )
            finally:
                router.close_pipe(receiver)

        self.assertEqual(listener.messages, messages)

    def test_event_loop_after_route_until(self):
        # This tests a potentially problematic situation:
        # - route_until processes at least one message manually
        # - the 'ping' for that message is still on the event loop
        # - when the event loop is started, it tries to get that same message
        #   from the message queue, but no such message exists, so we end
        #   up blocking forever.
        messages = ["abc"]

        with self.context.worker_pool() as worker_pool:
            with self.started_router() as router:
                sender, receiver = router.pipe()
                try:
                    listener = ReceiverListener(receiver=receiver)
                    worker_pool.submit(send_messages, sender, messages)
                    router.route_until(
                        lambda: len(listener.messages) >= len(messages),
                    )
                    self.exercise_event_loop()
                finally:
                    router.close_pipe(receiver)

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
