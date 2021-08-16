# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!


from traits.api import (
    HasStrictTraits,
    Instance,
    Int,
    List,
    observe,
    Str,
    Tuple,
    Union,
)

from traits_futures.api import (
    CANCELLED,
    COMPLETED,
    FAILED,
    IStepsReporter,
    StepsFuture,
    submit_steps,
)

#: Maximum timeout for blocking calls, in seconds. A successful test should
#: never hit this timeout - it's there to prevent a failing test from hanging
#: forever and blocking the rest of the test suite.
SAFETY_TIMEOUT = 5.0


#: Trait type for the progress state: total, complete, message.
ProgressState = Tuple(Union(None, Int()), Int(), Union(None, Str()))


class StepsListener(HasStrictTraits):
    """
    Listener recording all state changes for a StepsFuture.
    """

    #: The future we're listening to.
    future = Instance(StepsFuture)

    #: The progress state.
    state = Union(None, ProgressState)

    #: All recorded states, including the initial state.
    states = List(ProgressState)

    @observe("future.[total,complete,message]")
    def _record_state(self, event):
        future = event.new if event.name == "future" else event.object
        self.state = future.total, future.complete, future.message

    @observe("state")
    def _append_new_state(self, event):
        """Record the new state whenever it changes."""
        self.states.append(event.new)


class BackgroundStepsTests:
    def test_reporter_implements_i_steps_reporter(self):
        def check_steps_reporter_interface(reporter):
            return isinstance(reporter, IStepsReporter)

        future = submit_steps(
            self.executor, 0, "Checking", check_steps_reporter_interface
        )
        self.assertTaskEventuallyCompletes(future, True)

    def test_reporter_is_passed_by_name(self):
        def reporter_by_name(*, reporter):
            return 46

        future = submit_steps(
            self.executor, 0, "Doing nothing", reporter_by_name
        )
        self.assertTaskEventuallyCompletes(future, 46)

    def test_result(self):
        def return_a_value(reporter):
            return 45

        future = submit_steps(
            self.executor, 0, "Returning a value", return_a_value
        )
        self.assertTaskEventuallyCompletes(future, 45)

    def test_error(self):
        def raise_an_error(reporter):
            1 / 0

        future = submit_steps(self.executor, 0, "Raising", raise_an_error)
        self.assertTaskEventuallyFails(future, ZeroDivisionError)

    def test_state_changes_no_reports(self):
        def return_a_value(reporter):
            return 45

        future = submit_steps(
            self.executor, 0, "Doing nothing", return_a_value
        )
        listener = StepsListener(future=future)
        self.assertTaskEventuallyCompletes(future, 45)

        self.assertEqual(
            listener.states,
            [
                (0, 0, "Doing nothing"),
            ],
        )

    def test_simple_messages(self):
        def send_messages(reporter):
            reporter.step("Uploading file 1")
            reporter.step("Uploading file 2")
            reporter.stop("Finished")

        future = submit_steps(
            self.executor, 2, "Uploading files", send_messages
        )
        listener = StepsListener(future=future)
        self.assertTaskEventuallyCompletes(future, None)
        self.assertEqual(
            listener.states,
            [
                (2, 0, "Uploading files"),
                (2, 0, "Uploading file 1"),
                (2, 1, "Uploading file 2"),
                (2, 2, "Finished"),
            ],
        )

    def test_irregular_step_sizes(self):
        def send_messages(reporter):
            reporter.step("Uploading file 1", size=2)
            reporter.step("Uploading file 2", size=5)
            reporter.step("Uploading file 3", size=3)
            reporter.stop("Uploads complete")

        future = submit_steps(
            self.executor, 10, "Uploading files...", send_messages
        )
        listener = StepsListener(future=future)
        self.assertTaskEventuallyCompletes(future, None)
        self.assertEqual(
            listener.states,
            [
                (10, 0, "Uploading files..."),
                (10, 0, "Uploading file 1"),
                (10, 2, "Uploading file 2"),
                (10, 7, "Uploading file 3"),
                (10, 10, "Uploads complete"),
            ],
        )

    def test_no_stop(self):
        # If the user doesn't call stop, we don't get a final update, but
        # nothing else should go wrong.
        def send_messages(reporter):
            reporter.step("Uploading file 1")
            reporter.step("Uploading file 2")

        future = submit_steps(
            self.executor, 2, "Uploading files", send_messages
        )
        listener = StepsListener(future=future)
        self.assertTaskEventuallyCompletes(future, None)
        self.assertEqual(
            listener.states,
            [
                (2, 0, "Uploading files"),
                (2, 0, "Uploading file 1"),
                (2, 1, "Uploading file 2"),
            ],
        )

    def test_cancellation_on_step(self):
        barrier = self._context.event()
        detector = self._context.event()

        def send_messages(barrier, reporter, detector):
            reporter.step("Uploading file 1")
            # Test will cancel at this point.
            barrier.wait(timeout=SAFETY_TIMEOUT)
            reporter.step("Uploading file 2")
            # Should never get here.
            detector.set()
            reporter.stop("All files uploaded")

        future = submit_steps(
            self.executor,
            2,
            "Uploading files",
            send_messages,
            barrier=barrier,
            detector=detector,
        )
        listener = StepsListener(future=future)

        # Run until we get the first progress message, then cancel and allow
        # the background job to proceed.
        self.run_until(
            listener,
            "state",
            lambda listener: listener.state[2] == "Uploading file 1",
        )
        future.cancel()
        barrier.set()

        self.assertTaskEventuallyCancelled(future)
        self.assertFalse(detector.is_set())

        self.assertEqual(
            listener.states,
            [
                (2, 0, "Uploading files"),
                (2, 0, "Uploading file 1"),
            ],
        )

    def test_cancellation_on_stop(self):
        barrier = self._context.event()
        detector = self._context.event()

        def send_messages(barrier, reporter, detector):
            reporter.step("Uploading file 1")
            reporter.step("Uploading file 2")
            # Test will cancel at this point.
            barrier.wait(timeout=SAFETY_TIMEOUT)
            reporter.stop("All files uploaded"),
            # Should never get here.
            detector.set()

        future = submit_steps(
            self.executor,
            2,
            "Uploading files",
            send_messages,
            barrier=barrier,
            detector=detector,
        )
        listener = StepsListener(future=future)

        # Run until we get the first progress message, then cancel and allow
        # the background job to proceed.
        self.run_until(
            listener,
            "state",
            lambda listener: listener.state[2] == "Uploading file 2",
        )
        future.cancel()
        barrier.set()

        self.assertTaskEventuallyCancelled(future)
        self.assertFalse(detector.is_set())

        self.assertEqual(
            listener.states,
            [
                (2, 0, "Uploading files"),
                (2, 0, "Uploading file 1"),
                (2, 1, "Uploading file 2"),
            ],
        )

    def test_initial_total(self):
        # Exercise the case where we set the total and message up front.
        def send_messages(reporter):
            reporter.step("Uploading file 1")
            reporter.step("Uploading file 2")
            reporter.stop("All uploaded")

        future = submit_steps(
            self.executor, 2, "Uploading files", send_messages
        )
        listener = StepsListener(future=future)
        self.assertTaskEventuallyCompletes(future, None)
        self.assertEqual(
            listener.states,
            [
                (2, 0, "Uploading files"),
                (2, 0, "Uploading file 1"),
                (2, 1, "Uploading file 2"),
                (2, 2, "All uploaded"),
            ],
        )

    def test_reporter_in_kwargs(self):
        def some_callable(reporter):
            pass

        with self.assertRaises(TypeError):
            submit_steps(
                self.executor,
                2,
                "Uploading files",
                some_callable,
                reporter=None,
            )

    # Helper functions

    def halt_executor(self):
        """
        Wait for the executor to stop.
        """
        executor = self.executor
        executor.stop()
        self.run_until(executor, "stopped", lambda executor: executor.stopped)
        del self.executor

    def assertTaskEventuallyCompletes(self, future, result):
        """
        Wait for a task to finish, and check its return value.

        Parameters
        ----------
        future : BaseFuture
            The future to wait for.
        result : object
            Value that that task is expected to return.
        """
        self.run_until(future, "done", lambda future: future.done)
        self.assertEqual(future.state, COMPLETED)
        self.assertEqual(future.result, result)

    def assertTaskEventuallyFails(self, future, exception_type):
        """
        Wait for a task to finish, and verify that it fails.

        Parameters
        ----------
        future : BaseFuture
            The future to wait for.
        exception_type : type
            Type of the exception that the task is expected to raise.
        """
        self.run_until(future, "done", lambda future: future.done)
        self.assertEqual(future.state, FAILED)
        self.assertIn(exception_type.__name__, future.exception[0])

    def assertTaskEventuallyCancelled(self, future):
        """
        Wait for a task to finish, and check it reached CANCELLED state.

        Parameters
        ----------
        future : BaseFuture
            The future to wait for.
        """
        self.run_until(future, "done", lambda future: future.done)
        self.assertEqual(future.state, CANCELLED)
