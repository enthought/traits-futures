from __future__ import absolute_import, print_function, unicode_literals

import wx

from pyface.api import Window, GUI


class StealthyWindow(Window):
    """
    Subclass of Window that doesn't make itself visible.
    """
    def activate(self):
        self.control.Iconize(False)
        # Don't raise.

    def show(self, visible):
        self.control.Show(False)


class TimeoutTimer(wx.Timer):
    def __init__(self, on_timeout, timeout):
        wx.Timer.__init__(self)
        self.on_timeout = on_timeout
        self.Start(int(timeout*1e3), True)
        self.timed_out = False

    def Notify(self):
        self.timed_out = True
        self.on_timeout()

    def stop(self):
        if self.IsRunning():
            self.Stop()


class ConditionTimeoutError(RuntimeError):
    pass


class EventLoop(object):
    def __init__(self):
        self.loop_stopped = False
        self.gui = GUI()

    def start(self):
        # It seems to be necessary to have at least one Window object present
        # to keep the event loop running.
        window = StealthyWindow()
        window.open()
        self.gui.start_event_loop()

    def stop(self):
        if not self.loop_stopped:
            self.loop_stopped = True
            self.gui.stop_event_loop()


class GuiTestAssistant(object):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def run_until_condition(self, object, trait, condition, timeout=10.0):
        """
        Run the event loop until the given condition holds true. The condition
        is evaluated whenever object.trait changes, and takes the object as a
        parameter.

        Raise if the condition never becomes true.
        """
        if condition(object):
            return

        def stop_event_loop_on_condition(object, name, new):
            if condition(object):
                event_loop.stop()

        event_loop = EventLoop()
        timer = TimeoutTimer(event_loop.stop, timeout)
        try:
            object.on_trait_change(stop_event_loop_on_condition, trait)
            try:
                event_loop.start()
            finally:
                object.on_trait_change(
                    stop_event_loop_on_condition, trait, remove=True)
        finally:
            timer.stop()

        if timer.timed_out:
            raise ConditionTimeoutError(
                "Timed out after {} seconds.".format(timeout))
