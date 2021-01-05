..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!

Making tasks interruptible
==========================

All background tasks are cancellable in some form: calling the |cancel| method
on the future for the task requests cancellation of the background task.
However, for a basic callable submitted using |submit_call|, the ability to
cancel is rather crude. If cancellation is requested *before* the background
task starts executing, then as expected, the callable will not be executed.
However, once the background task starts executing, there's no safe way to
unilaterally interrupt it. So if cancellation occurs after execution starts,
the callable still runs to completion, and only once it's completed does the
state of the corresponding future change from |CANCELLING| to |CANCELLED|.

To allow cancellation to *interrupt* a background task mid-calculation, the
background task must cooperate, meaning that the code for that task must be
modified. Fortunately, that modification can be very simple.

This section describes how to modify the callable for a background task to make
it possible to interrupt mid-calculation. In brief, you turn your callable into
a |generator function| by inserting |yield| statements representing possible
interruption points, and then execute that callable using |submit_iteration|
instead of |submit_call|. In addition, each |yield| statement can be used to
provide progress information to the future. The following goes into this in
more detail.

Example: approximating π
------------------------

We use a simplistic example to illustrate. The following code uses a Monte
Carlo algorithm to compute (slowly and inefficiently) an approximation to π.

.. code-block:: python

    import random

    def approximate_pi(sample_count=10 ** 8):
        # approximate pi/4 by throwing points at a unit square and
        # counting the proportion that land in the quarter circle.
        inside = total = 0
        for _ in range(sample_count):
            x, y = random.random(), random.random()
            inside += x * x + y * y < 1
            total += 1
        return 4 * inside / total

On a typical laptop or desktop machine, one would expect this function call to
take on the order of several seconds to execute. If this callable is submitted
to an executor via |submit_call| in a TraitsUI GUI, and then cancelled by the
user after execution has started, the future may not move from |CANCELLING| to
|CANCELLED| state until several seconds after cancellation is requested. Note,
however, that the GUI will remain responsive and usable during those seconds.

Here's a complete TraitsUI application that demonstrates this behaviour.

.. literalinclude:: examples/non_interruptible_task.py

However, with two simple changes, we can allow the ``approximate_pi`` function
to cancel mid-calculation. Those two changes are:

- insert a |yield| statement at possible interruption points
- submit the background task via |submit_iteration| instead of |submit_call|.

The implementation of |submit_iteration| not only checks for cancellation, but
also sends a message to the future at every |yield| point. For that reason, you
don't want to yield too often - as a guide, sending a message more than 100
times per second is likely be inefficient. But conversely, if you yield too
rarely, then the checks for cancellation will be spaced further apart, so you
increase the latency for a response to a cancellation request.

Making the approximation cancellable
------------------------------------

Here's a modification of the above function that checks for cancellation every
100 thousand iterations (which, for reference, worked out to around every 50th
of a second when tested on a high-end 2018 laptop). It adds just two lines to
the original function.

.. code-block:: python
    :emphasize-lines: 6-7

    def approximate_pi(sample_count=10 ** 8):
        # approximate pi/4 by throwing points at a unit square and
        # counting the proportion that land in the quarter circle.
        inside = total = 0
        for i in range(sample_count):
            if i % 10 ** 5 == 0:
                yield  # <- allow interruption here
            x, y = random.random(), random.random()
            inside += x * x + y * y < 1
            total += 1
        return 4 * inside / total

Adding the |yield| changes the function type: it's now a Python |generator
function|, returning a |generator| when called. So we need to use
|submit_iteration| instead of |submit_call| to send this function to the
executor, and we get an |IterationFuture| instead of a |CallFuture| in return.
Just as with the |CallFuture|, the eventual result of the ``approximate_pi``
call is supplied to the future on completion via the |result| attribute.

Sending partial results
-----------------------

As we mentioned above, |submit_iteration| also sends a message to the
|IterationFuture| whenever it encounters a |yield|. That message carries
whatever was yielded as a payload. That means that we can replace the plain
|yield| to yield an expression, providing information to the future. That
information could contain progress information, partial results, log messages,
or any useful information you want to provide (though ideally, whatever Python
object you yield should be both immutable and pickleable). Every time you do a
``yield something`` in the iteration, that ``something`` is assigned to the
|result_event| trait on the |IterationFuture| object, making it easy to listen
for those results.

Here's a version of the approximation code that yields partial results at each
|yield| point.

.. code-block:: python
    :emphasize-lines: 6-7

    def approximate_pi(sample_count=10 ** 8):
        # approximate pi/4 by throwing points at a unit square and
        # counting the proportion that land in the quarter circle.
        inside = total = 0
        for i in range(sample_count):
            if i > 0 and i % 10 ** 5 == 0:
                yield 4 * inside / total  # <- partial result
            x, y = random.random(), random.random()
            inside += x * x + y * y < 1
            total += 1
        return 4 * inside / total


Here's a complete TraitsUI example making use of the above.

.. literalinclude:: examples/interruptible_task.py

..
   substitutions

.. |CallFuture| replace:: :class:`~traits_futures.background_call.CallFuture`
.. |cancel| replace:: :meth:`~traits_futures.base_future.BaseFuture.cancel`
.. |CANCELLED| replace:: :data:`~traits_futures.future_states.CANCELLED`
.. |CANCELLING| replace:: :data:`~traits_futures.future_states.CANCELLING`
.. |generator| replace:: :term:`generator <generator iterator>`
.. |generator function| replace:: :term:`generator function <generator>`
.. |IterationFuture| replace:: :class:`~traits_futures.background_iteration.IterationFuture`
.. |result| replace:: :attr:`~traits_futures.base_future.BaseFuture.result`
.. |result_event| replace:: :attr:`~traits_futures.background_iteration.IterationFuture.result_event`
.. |submit_call| replace:: :func:`~traits_futures.background_call.submit_call`
.. |submit_iteration| replace:: :func:`~traits_futures.background_iteration.submit_iteration`
.. |yield| replace:: :ref:`yield <yield>`
