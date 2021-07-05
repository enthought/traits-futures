# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!


from traits.api import HasStrictTraits, Instance, List, on_trait_change, Str

from traits_futures.api import IStepsReporter, StepsFuture, submit_steps


def check_steps_reporter_interface(progress):
    """
    Check that 'progress' has been declared to support the right interface.
    """
    if not isinstance(progress, IStepsReporter):
        raise RuntimeError()
    else:
        return True


class StepsListener(HasStrictTraits):
    """
    Listener recording state changes for a StepsFuture.
    """

    messages = List(Str)

    future = Instance(StepsFuture)

    @on_trait_change("future:message")
    def _update_messages(self, message):
        self.messages.append(message)


class BackgroundStepsTests:
    def test_progress_implements_i_steps_reporter(self):
        future = submit_steps(self.executor, check_steps_reporter_interface)
        self.wait_until_done(future)

        self.assertResult(future, True)
        self.assertNoException(future)

    def test_simple_messages(self):
        def send_messages(self, progress):
            progress.start("Uploading files")
            progress.step("Uploaded file 1")
            progress.step("Uploaded file 2")

        future = submit_steps(self.executor, send_messages)
        listener = StepsListener(future=future)
        self.wait_until_done(future)

        self.assertEqual(
            listener.messages,
            ["Uploading files", "Uploaded file 1", "Uploaded file 2"],
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

    def wait_until_done(self, future):
        self.run_until(future, "done", lambda future: future.done)

    # Assertions

    def assertResult(self, future, expected_result):
        self.assertEqual(future.result, expected_result)

    def assertNoException(self, future):
        with self.assertRaises(AttributeError):
            future.exception
