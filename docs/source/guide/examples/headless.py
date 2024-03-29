# (C) Copyright 2018-2024 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Running Traits Futures without a GUI, using the asyncio event loop.
"""

import asyncio
import random

from traits_futures.api import (
    AsyncioEventLoop,
    submit_iteration,
    TraitsExecutor,
)


def approximate_pi(sample_count=10**8, report_interval=10**6):
    """
    Yield successive approximations to π via Monte Carlo methods.
    """
    # approximate pi/4 by throwing points at a unit square and
    # counting the proportion that land in the quarter circle.
    inside = total = 0
    for i in range(sample_count):
        if i > 0 and i % report_interval == 0:
            yield 4 * inside / total  # <- partial result
        x, y = random.random(), random.random()
        inside += x * x + y * y < 1
        total += 1
    return 4 * inside / total


async def future_wrapper(traits_future):
    """
    Wrap a Traits Futures future as a schedulable coroutine.
    """

    def set_result(event):
        traits_future = event.object
        asyncio_future.set_result(traits_future.result)

    asyncio_future = asyncio.get_running_loop().create_future()

    traits_future.observe(set_result, "done")

    return await asyncio_future


def print_progress(event):
    """
    Progress reporter for the π calculation.
    """
    print(f"π is approximately {event.new:.6f}")


if __name__ == "__main__":
    asyncio_event_loop = asyncio.new_event_loop()
    traits_executor = TraitsExecutor(
        event_loop=AsyncioEventLoop(event_loop=asyncio_event_loop)
    )
    traits_future = submit_iteration(traits_executor, approximate_pi)
    traits_future.observe(print_progress, "result_event")

    asyncio_event_loop.run_until_complete(future_wrapper(traits_future))
