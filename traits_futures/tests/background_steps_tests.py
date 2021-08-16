# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!


from traits.api import HasStrictTraits, Instance, List, observe

from traits_futures.api import (
    CANCELLED,
    COMPLETED,
    FAILED,
    IStepsReporter,
    StepsFuture,
    submit_steps,
)
from traits_futures.exception_handling import _qualified_type_name

#: Maximum timeout for blocking calls, in seconds. A successful test should
#: never hit this timeout - it's there to prevent a failing test from hanging
#: forever and blocking the rest of the test suite.
SAFETY_TIMEOUT = 5.0


class StepsListener(HasStrictTraits):
    """
    Listener recording all state changes for a StepsFuture.
    """

    messages = List()

    future = Instance(StepsFuture)

    @observe("future")
    def _capture_initial_state(self, event):
        future = event.new
        self.messages.append(("message", future.message))
        self.messages.append(("total", future.total))
        self.messages.append(("complete", future.complete))

    @observe("future:message,future:total,future:complete")
    def _update_messages(self, event):
        self.messages.append((event.name, event.new))


# State is:
# - total: total work, in whatever units make sense
# - complete: units of work complete
# - message: description of step currently in progress

# XXX Simplest use-case: no calls to progress at all; just a long-running task.
# XXX Next simplest: progress.step("uploading file 1"),
#     progress.step("uploading file 2")
# XXX Next simplest: progress.total = 2; progress.step("..."),
#     progress.step("...")
# XXX Advanced: progress.sync() / progress.update() / .... after manual
#     changes.

# XXX Does the steps reporter actually _need_ to be a `HasStrictTraits` class?


class BackgroundStepsTests:
    def test_reporter_implements_i_steps_reporter(self):
        def check_steps_reporter_interface(reporter):
            return isinstance(reporter, IStepsReporter)

        future = submit_steps(
            self.executor, None, None, check_steps_reporter_interface
        )
        result = self.wait_for_result(future)
        self.assertTrue(result)

    def test_reporter_is_passed_by_name(self):
        def reporter_by_name(*, reporter):
            return 46

        future = submit_steps(self.executor, None, None, reporter_by_name)
        self.assertEqual(self.wait_for_result(future), 46)

    def test_result(self):
        def return_a_value(reporter):
            return 45

        future = submit_steps(self.executor, None, None, return_a_value)
        self.assertEqual(self.wait_for_result(future), 45)

    def test_error(self):
        def raise_an_error(reporter):
            1 / 0

        future = submit_steps(self.executor, None, None, raise_an_error)
        self.assertEqual(
            self.wait_for_exception(future),
            _qualified_type_name(ZeroDivisionError),
        )

    def test_state_changes_no_reports(self):
        def return_a_value(reporter):
            return 45

        future = submit_steps(self.executor, None, None, return_a_value)
        listener = StepsListener(future=future)
        self.wait_for_result(future)

        expected_messages = [
            dict(message=None, total=None, complete=0),
        ]
        self.check_messages(listener.messages, expected_messages)

    def test_initial_values(self):
        def do_nothing(reporter):
            return 23

        future = submit_steps(self.executor, None, None, do_nothing)

        self.assertIsNone(future.message)
        self.assertIsNone(future.total)
        self.assertEqual(future.complete, 0)

        result = self.wait_for_result(future)
        self.assertEqual(result, 23)

    def test_simple_messages(self):
        def send_messages(reporter):
            reporter.step("Uploading file 1")
            reporter.step("Uploading file 2")
            reporter.stop("Finished")

        future = submit_steps(self.executor, None, None, send_messages)
        listener = StepsListener(future=future)
        self.wait_for_result(future)

        expected_messages = [
            # Initial values
            dict(message=None, total=None, complete=0),
            # Updates on start of first step
            dict(message="Uploading file 1"),
            # Updates on start of second step
            dict(message="Uploading file 2", complete=1),
            # Updates on completion.
            dict(message="Finished", complete=2),
        ]
        self.check_messages(listener.messages, expected_messages)

    def test_set_total(self):
        def send_messages(reporter):
            reporter.start(total=2)
            reporter.step("Uploading file 1")
            reporter.step("Uploading file 2")
            reporter.stop("All done")

        future = submit_steps(self.executor, None, None, send_messages)
        listener = StepsListener(future=future)
        self.wait_for_result(future)

        expected_messages = [
            # Initial values
            dict(message=None, total=None, complete=0),
            # Updates on setting 'total' to 2.
            dict(total=2),
            # Updates on start of first step
            dict(message="Uploading file 1"),
            # Updates on start of second step
            dict(message="Uploading file 2", complete=1),
            # Updates on completion.
            dict(message="All done", complete=2),
        ]
        self.check_messages(listener.messages, expected_messages)

    def test_irregular_step_sizes(self):
        def send_messages(reporter):
            reporter.start("Uploading files...", total=10)
            reporter.step("Uploading file 1", size=2)
            reporter.step("Uploading file 2", size=5)
            reporter.step("Uploading file 3", size=3)
            reporter.stop("Uploads complete")

        future = submit_steps(self.executor, None, None, send_messages)
        listener = StepsListener(future=future)
        self.wait_for_result(future)

        expected_messages = [
            dict(message=None, total=None, complete=0),
            dict(message="Uploading files...", total=10),
            dict(message="Uploading file 1"),
            dict(message="Uploading file 2", complete=2),
            dict(message="Uploading file 3", complete=7),
            dict(message="Uploads complete", complete=10),
        ]
        self.check_messages(listener.messages, expected_messages)

    def test_no_stop(self):
        # If the user doesn't call stop, we should still get a final update
        # that sets the 'step'.
        def send_messages(reporter):
            reporter.start(total=2)
            reporter.step("Uploading file 1")
            reporter.step("Uploading file 2")

        future = submit_steps(self.executor, None, None, send_messages)
        listener = StepsListener(future=future)
        self.wait_for_result(future)

        expected_messages = [
            # Initial values
            dict(message=None, total=None, complete=0),
            # Updates on setting 'total' to 2.
            dict(total=2),
            # Updates on start of first step
            dict(message="Uploading file 1"),
            # Updates on start of second step
            dict(message="Uploading file 2", complete=1),
            # Updates on completion.
            dict(complete=2),
        ]

        self.check_messages(listener.messages, expected_messages)

    # XXX test cancellation on start, and cancellation on stop

    def test_cancellation_on_step(self):
        checkpoint = self._context.event()
        barrier = self._context.event()
        detector = self._context.event()

        def send_messages(checkpoint, barrier, reporter, detector):
            reporter.start(total=2)
            reporter.step("Uploading file 1")
            checkpoint.set()
            # Test will cancel at this point.
            barrier.wait(timeout=SAFETY_TIMEOUT)
            # Call to 'step' should abandon execution.
            reporter.step("Uploading file 2")
            detector.set()

        future = submit_steps(
            self.executor,
            None,
            None,
            send_messages,
            checkpoint=checkpoint,
            barrier=barrier,
            detector=detector,
        )
        listener = StepsListener(future=future)

        checkpoint.wait(timeout=SAFETY_TIMEOUT)
        future.cancel()
        barrier.set()

        self.wait_for_cancelled(future)

        self.assertFalse(detector.is_set())

        expected_messages = [
            # Initial values
            dict(message=None, total=None, complete=0),
        ]
        self.check_messages(listener.messages, expected_messages)

    def test_initial_total(self):
        # Exercise the case where we set the total and message up front.
        def send_messages(reporter):
            reporter.step("Uploading file 1")
            reporter.step("Uploading file 2")

        future = submit_steps(
            self.executor, 2, "Uploading files", send_messages
        )
        listener = StepsListener(future=future)
        self.wait_for_result(future)

        expected_messages = [
            # Initial values
            dict(message="Uploading files", total=2, complete=0),
            # Updates on start of first step
            dict(message="Uploading file 1"),
            # Updates on start of second step
            dict(message="Uploading file 2", complete=1),
            # Updates on completion.
            dict(complete=2),
        ]

        self.check_messages(listener.messages, expected_messages)

    def check_messages(self, actual_messages, expected_messages):

        actual_messages = actual_messages.copy()

        # Expected messages should match actual messages, in chunks
        for message_set in expected_messages:
            message_count = len(message_set)
            self.assertCountEqual(
                actual_messages[:message_count],
                list(message_set.items()),
            )
            actual_messages = actual_messages[message_count:]

        # Check we got everything.
        self.assertFalse(actual_messages)

    # Helper functions

    def halt_executor(self):
        """
        Wait for the executor to stop.
        """
        executor = self.executor
        executor.stop()
        self.run_until(executor, "stopped", lambda executor: executor.stopped)
        del self.executor

    def wait_for_result(self, future):
        self.run_until(future, "done", lambda future: future.done)
        if future.state == COMPLETED:
            return future.result
        elif future.state == FAILED:
            exc_type, exc_value, exc_traceback = future.exception
            self.fail(
                f"Task failed with exception of type: {exc_type}\n"
                f"{exc_traceback}"
            )
        elif future.state == CANCELLED:
            self.fail("Task did not return a result because it was cancelled.")

    def wait_for_exception(self, future):
        self.run_until(future, "done", lambda future: future.done)
        exc_type, exc_value, exc_traceback = future.exception
        return exc_type

    def wait_for_cancelled(self, future):
        self.run_until(future, "done", lambda future: future.done)
        if future.state != CANCELLED:
            raise RuntimeError("Future was not cancelled")
