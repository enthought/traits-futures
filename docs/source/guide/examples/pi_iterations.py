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
Example showing a background iteration that produces successive
approximations to pi, with resulting values being used to update
a Chaco plot.

Note: this example requires NumPy and Chaco.
"""
import numpy as np

from chaco.api import ArrayPlotData, Plot
from chaco.overlays.coordinate_line_overlay import CoordinateLineOverlay
from enable.component_editor import ComponentEditor
from traits.api import (
    Bool,
    Button,
    Float,
    HasStrictTraits,
    Instance,
    Int,
    List,
    observe,
    Property,
    Tuple,
)
from traits_futures.api import (
    IterationFuture,
    submit_iteration,
    TraitsExecutor,
)
from traitsui.api import HGroup, Item, UItem, VGroup, View


def pi_iterations(chunk_size):
    """
    Generate successive approximations to pi via a Monte Carlo method.

    Infinite iterator producing successive approximations to pi, via the usual
    Monte-Carlo method: generate random points in a square, and count the
    proportion that lie in an inscribed circle.

    Parameters
    ----------
    chunk_size : int
        The number of points to sample on each iteration.

    Yields
    ------
    result : tuple (int, float, float)
        Tuple containing:
        - the number of points generated
        - the approximation to pi
        - a two-sided error giving a ~95% confidence interval on the
          approximation.
    """
    nsamples = ninside = 0

    while True:
        samples = np.random.random(size=(chunk_size, 2))
        nsamples += chunk_size
        ninside += int(np.sum((samples * samples).sum(axis=1) <= 1.0))

        # Compute approximation along with a two-sided error giving
        # a ~95% confidence interval on that approximation.
        #
        # We use a normal approximation interval. See wikipedia for details:
        # https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        approximation = 4 * ninside / nsamples
        noutside = nsamples - ninside
        error = 7.839856 * np.sqrt(ninside * noutside / (nsamples ** 3))
        yield nsamples, approximation, error


class PiIterator(HasStrictTraits):
    """
    View and plot of pi approximation running in the background.
    """

    #: The Traits executor for the background jobs.
    traits_executor = Instance(TraitsExecutor)

    #: Chunk size to use for the approximations.
    chunk_size = Int(1000000)

    #: Calculation future.
    future = Instance(IterationFuture)

    #: Results arriving from the future.
    results = List(Tuple(Int(), Float(), Float()))

    #: Button to start the pi approximation.
    approximate = Button()

    #: Is the approximate button enabled?
    approximate_enabled = Property(Bool(), observe="future.state")

    #: Button to cancel the pi approximation.
    cancel = Button()

    #: Is the cancel button enabled?
    cancel_enabled = Property(Bool(), observe="future.state")

    #: Maximum number of points to show in the plot.
    max_points = Int(100)

    #: Data for the plot.
    plot_data = Instance(ArrayPlotData, ())

    #: The plot.
    plot = Instance(Plot)

    @observe("approximate")
    def _calculate_pi_approximately(self, event):
        self.future = submit_iteration(
            self.traits_executor, pi_iterations, chunk_size=self.chunk_size
        )

    @observe("cancel")
    def _cancel_future(self, event):
        self.future.cancel()

    @observe("future")
    def _reset_results(self, event):
        self.results = []

    @observe("future:result_event")
    def _record_result(self, event):
        result = event.new
        self.results.append(result)
        self._update_plot_data()

    def _get_approximate_enabled(self):
        return self.future is None or self.future.done

    def _get_cancel_enabled(self):
        return self.future is not None and self.future.cancellable

    def _update_plot_data(self):
        recent_results = self.results[-self.max_points :]  # noqa: E203
        # We need the reshape for the case where the results list is empty.
        results = np.array(recent_results).reshape((-1, 3))
        counts, approx, errors = results.T
        self.plot_data.update_data(
            counts=counts / 1e6,
            approx=approx,
            upper=approx + errors,
            lower=approx - errors,
        )

    def _plot_default(self):
        plot = Plot(self.plot_data)
        self._update_plot_data()
        plot.plot(("counts", "approx"), color="red")
        plot.plot(("counts", "upper"), color="gray")
        plot.plot(("counts", "lower"), color="gray")
        plot.x_axis.title = "Counts (millions of points)"
        plot.y_axis.title = "Approximation"

        # Add dashed horizontal line at pi.
        pi_line = CoordinateLineOverlay(
            component=plot,
            value_data=[np.pi],
            color="green",
            line_style="dash",
        )
        plot.underlays.append(pi_line)

        # Allow extra room for the y-axis label.
        plot.padding_left = 100

        return plot

    def default_traits_view(self):
        return View(
            HGroup(
                UItem("plot", editor=ComponentEditor()),
                VGroup(
                    Item("chunk_size"),
                    Item("max_points"),
                    UItem("approximate", enabled_when="approximate_enabled"),
                    UItem("cancel", enabled_when="cancel_enabled"),
                ),
            ),
            resizable=True,
        )


if __name__ == "__main__":
    traits_executor = TraitsExecutor()
    try:
        view = PiIterator(traits_executor=traits_executor)
        view.configure_traits()
    finally:
        traits_executor.shutdown()
