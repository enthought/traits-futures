# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Example showing a background iteration that produces successive
approximations to pi, with resulting values being used to update
a Chaco plot.

Note: this example requires NumPy and Chaco.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import numpy as np

from chaco.api import ArrayPlotData, Plot
from chaco.overlays.coordinate_line_overlay import CoordinateLineOverlay
from enable.component_editor import ComponentEditor
from traits.api import (
    Bool, Button, Float, Instance, Int, List, on_trait_change, Property, Tuple)
from traitsui.api import Handler, HGroup, Item, UItem, VGroup, View

from traits_futures.api import (
    IterationFuture,
    TraitsExecutor,
)


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
        ninside += np.sum((samples * samples).sum(axis=1) <= 1.0)

        # Compute approximation along with a two-sided error giving
        # a ~95% confidence interval on that approximation.
        #
        # We use a normal approximation interval. See wikipedia for details:
        # https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        approximation = 4 * ninside / nsamples
        noutside = nsamples - ninside
        error = 7.839856 * np.sqrt(ninside * noutside / (nsamples**3))
        yield nsamples, approximation, error


class PiIterator(Handler):
    """
    View and plot of pi approximation running in the background.
    """
    #: The Traits executor for the background jobs.
    traits_executor = Instance(TraitsExecutor, ())

    #: Chunk size to use for the approximations.
    chunk_size = Int(1000000)

    #: Calculation future.
    future = Instance(IterationFuture)

    #: Results arriving from the future.
    results = List(Tuple(Int(), Float(), Float()))

    #: Button to start the pi approximation.
    approximate = Button()

    #: Is the approximate button enabled?
    approximate_enabled = Property(Bool(), depends_on='future.state')

    #: Button to cancel the pi approximation.
    cancel = Button()

    #: Is the cancel button enabled?
    cancel_enabled = Property(Bool(), depends_on='future.state')

    #: Maximum number of points to show in the plot.
    max_points = Int(100)

    #: Data for the plot.
    plot_data = Instance(ArrayPlotData, ())

    #: The plot.
    plot = Instance(Plot)

    def closed(self, info, is_ok):
        # Stopping the executor cancels any running future.
        self.traits_executor.stop()
        super(PiIterator, self).closed(info, is_ok)

    def _approximate_fired(self):
        self.future = self.traits_executor.submit_iteration(
            pi_iterations, chunk_size=self.chunk_size)

    def _cancel_fired(self):
        self.future.cancel()

    @on_trait_change('future')
    def _reset_results(self):
        self.results = []

    @on_trait_change('future:result_event')
    def _record_result(self, result):
        self.results.append(result)
        self._update_plot_data()

    def _get_approximate_enabled(self):
        return self.future is None or self.future.done

    def _get_cancel_enabled(self):
        return self.future is not None and self.future.cancellable

    def _update_plot_data(self):
        # We need the reshape for the case where the results list is empty.
        results = np.array(self.results[-self.max_points:]).reshape((-1, 3))
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
                UItem('plot', editor=ComponentEditor()),
                VGroup(
                    Item('chunk_size'),
                    Item('max_points'),
                    UItem(
                        'approximate',
                        enabled_when='approximate_enabled',
                    ),
                    UItem(
                        'cancel',
                        enabled_when='cancel_enabled',
                    ),
                ),
            ),
            resizable=True,
        )


if __name__ == '__main__':
    view = PiIterator()
    view.configure_traits()
