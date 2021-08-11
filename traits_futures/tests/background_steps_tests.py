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

from traits_futures.api import IStepsReporter, StepsFuture, submit_steps


def check_steps_reporter_interface(progress):
    """
    Check that 'progress' has been declared to support the right interface.
    """
    return isinstance(progress, IStepsReporter)


class StepsListener(HasStrictTraits):
    """
    Listener recording all state changes for a StepsFuture.
    """

    messages = List()

    future = Instance(StepsFuture)

    @observe("future:message,future:step,future:steps")
    def _update_messages(self, event):
        self.messages.append((event.name, event.new))


# Consider (a) storing the state on the StepsReporter, so that it can be
# accessed directly by the writer of the function, and then (b) there
# can be a single simple message type which sends the state (message, step, steps)
# to the foreground. We can add helper functions to do things like increment
# the step and set a new message all at the same time.

# State is:
# - step: number of completed steps
# - steps: total number of steps
# - message: description of step currently in progress

# XXX Simplest use-case: no calls to progress at all; just a long-running task.
# XXX Next simplest: progress.step("uploading file 1"), progress.step("uploading file 2")
# XXX Next simplest: progress.steps = 2; progress.step("..."), progress.step("...")
# XXX Advanced: progress.sync() / progress.update() / .... after manual changes.

# XXX Does the steps reporter actually _need_ to be a `HasStrictTraits` class?


class BackgroundStepsTests:
    def test_progress_implements_i_steps_reporter(self):
        future = submit_steps(self.executor, check_steps_reporter_interface)
        result = self.wait_for_result(future)
        self.assertTrue(result)

    def test_initial_values(self):
        def do_nothing(progress):
            return 23

        future = submit_steps(self.executor, do_nothing)

        self.assertIsNone(future.message)
        self.assertIsNone(future.steps)
        self.assertEqual(future.step, 0)

        result = self.wait_for_result(future)
        self.assertEqual(result, 23)

    def test_simple_messages(self):
        def send_messages(progress):
            progress.step("Uploading file 1")
            progress.step("Uploading file 2")

        future = submit_steps(self.executor, send_messages)
        listener = StepsListener(future=future)
        self.wait_for_result(future)

        expected_messages = [
            dict(message="Uploading file 1", step=0),
            dict(message="Uploading file 2", step=1),
        ]

        actual_messages = listener.messages

        # self.assertEqual(expected_messages, actual_messages)

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
        return future.result
