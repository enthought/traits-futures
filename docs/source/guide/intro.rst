..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!

Introduction
============

In this guide we'll introduce the key players in the |traits_futures|
package. All classes and data items mentioned here can be imported directly
from the |traits_futures.api| module.

Submitting background tasks
---------------------------

The |TraitsExecutor| is the main point of entry to |traits_futures|. Its job is
to accept one or more task submissions. For each task submitted, it sends the
computation to run in the background on a worker from a worker pool, and
returns a corresponding "future" object that allows monitoring of the state of
the background computation and retrieval of its results.

We'll examine the future objects in the next section. This section deals with
the executor's main top-level methods and the task submission functions.

To submit a task, use one of the convenience submission functions available
from |traits_futures.api|:

- The |submit_call| function allows submission of a simple Python callable,
  with given positional and named arguments. For example::

    submit_call(my_executor, int, "10101", base=2)

  will execute ``int("10101", base=2)`` in the background. |submit_call|
  doesn't wait for the background task to finish; instead, it immediately
  returns a |CallFuture| object. See the next section for more details on
  the |CallFuture| and related objects.

- The |submit_iteration| function allows submission of an arbitrary iterable.
  The user provides a callable which, when called, returns an iterable object.
  For example::

    submit_iteration(my_executor, range, 0, 5)

  It returns an |IterationFuture| object.

- The |submit_progress| function allows submission of a progress-reporting
  callable, and returns a |ProgressFuture| object. The callable submitted
  *must* have a parameter called "progress".  A value for this parameter will
  be passed (by name) by the executor machinery. The value passed for the
  "progress" parameter can then be called to send progress reports to the
  associated |ProgressFuture| object. If the future has been cancelled, the
  next call to ``progress`` in the background task will raise a
  |ProgressCancelled| exception.

  For example, your callable might look like this::

    def interruptible_sum_of_squares(n, progress):
        """ Compute the sum of squares of integers smaller than n."""
        total = 0
        for i in range(n):
            # Send a pair of the form (steps_completed, total_steps)
            progress((i, n))
            total += i*i
        progress((n, n))

  The computation consists of ``n`` steps: a progress report is sent before
  each step, and after the end of the computation. The ``progress`` callable
  accepts a single Python object, but of course that Python object can be a
  compound object like a :class:`tuple` or a :class:`dict`. It's up to you to
  choose the format of the objects you want to send. They'll arrive in exactly
  the same format in the |ProgressFuture|, and then your application can choose
  how to interpret them.

In the current version of Traits Futures, tasks may only be submitted from the
main thread. An attempt to submit a task from a background thread will raise
|RuntimeError|. This restriction may be removed in the future.


Working with future objects
---------------------------

The various submission methods described above are asynchronous: they return a
"future" object immediately without waiting for the background task to
complete. The returned "future" has three purposes:

- it provides information about the current state of the background task
- it provides results from the background task (or exception information in the
  case of failure)
- it provides a way to request that a background task be cancelled

In this section we describe these three topics in more detail.


Future states
~~~~~~~~~~~~~

The |CallFuture|, |IterationFuture| and |ProgressFuture| objects all provide a
|future_state| trait, of trait type |FutureState|, that represents the state of
the underlying computation. That state has one of six possible different
values:

|WAITING|
   The background task has been scheduled to run, but has not yet started
   executing (for example, because the worker pool is still busy dealing
   with previously-submitted tasks.

|EXECUTING|
   The background task is currently executing on one of the workers.

|COMPLETED|
   The background task has completed without error. For a progress task or a
   simple call, this implies that a result has been returned and is available
   via the |result| property of the future. For an iteration, it means that
   the iteration has completed.

|FAILED|
   The background task raised an exception at some point in its execution.
   Information about the exception is available via the |exception| property
   of the future.

|CANCELLING|
   Cancellation of the background task has been requested, but the background
   task has not yet acknowledged that request.

|CANCELLED|
   The task has stopped following a cancellation request.

In addition, there are two traits whose values are derived from the
|future_state| trait: the |done| trait is ``True`` when |future_state| is one
of |COMPLETED|, |FAILED| or |CANCELLED|, and the |cancellable| trait is
``True`` when |future_state| is one of |WAITING| or |EXECUTING|.

It's important to understand that the |future_state| trait represents the state
of the background task *to the best of knowledge* of the main thread. For
example, when the background task starts executing, it sends a message to the
corresponding future telling it to change its state from |WAITING| to
|EXECUTING|. However, that message won't necessarily get processed immediately,
so there will be a brief interval during which the background task has, in
fact, started executing, but the state of the future is still |WAITING|.

Here's a diagram showing the possible state transitions. The initial state
is |WAITING|. The final states are |CANCELLED|, |COMPLETED| and |FAILED|.
The future expects to receive either the message sequence ``["started",
"raised"]`` or the message sequence ``["started", "returned"]`` from the
background task: this happens even if cancellation is requested.

.. graphviz::

   digraph FutureStates {
       WAITING -> EXECUTING [label="started"];
       WAITING -> CANCELLING [label="cancel"];
       CANCELLING -> CANCELLING [label="started"];
       EXECUTING -> FAILED [label="raised"];
       EXECUTING -> COMPLETED [label="returned"];
       EXECUTING -> CANCELLING [label="cancel"];
       CANCELLING -> CANCELLED [label="raised"];
       CANCELLING -> CANCELLED [label="returned"];
   }



Getting task results
~~~~~~~~~~~~~~~~~~~~

Background task results can be retrieved directly from the corresponding
futures.

The |submit_call| and |submit_progress| functions run callables that eventually
expect to return a result. Once the state of the corresponding future reaches
|COMPLETED|, the result of the call is available via the |result| attribute.
Assuming that your calculation future is stored in a trait called ``future``,
you might use this as follows::

    @observe('future:done')
    def _update_result(self, event):
        future = event.object
        self.my_results.append(future.result)

Any attempt to access the future's |result| before the future completes
successfully will raise an |AttributeError|. This includes the cases where
the background task was cancelled, or failed with an exception, as well
as the cases where the task is still executing or has yet to start running.

A |ProgressFuture| object also receives progress information send by the
background task via its |progress| event trait. You might use that
trait like this::

    @observe('future:progress')
    def _report_progress(self, event):
        progress_info = event.new
        current_step, max_steps, matches = progress_info
        self.message = "{} of {} chunks processed. {} matches so far".format(
            current_step, max_steps, matches)

The |submit_iteration| function is a little bit different: it produces a result
on each iteration, but doesn't necessarily give a final result. Its
|result_event| is an |Event| trait that you can hook
listeners up to in order to receive the iteration results. For example::

    @observe('future:result_event')
    def _record_result(self, event):
        result = event.new
        self.results.append(result)
        self.update_plot_data()

If a background task fails with an exception, then the corresponding future
eventually reaches |FAILED| state. In that case, information about the
exception that occurred is available in the future's |exception| attribute.
This information takes the form of a tuple of length 3, containing stringified
versions of the exception type, the exception value and the exception
traceback.

As with |result|, an attempt to access |exception| for a future that's not in
|FAILED| state will give an |AttributeError|.


Cancelling the background task
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The |CallFuture|, |IterationFuture| and |ProgressFuture| classes all have a
|cancel| method that allows the user to request cancellation of the
corresponding background task. That request gets interpreted a little
differently depending on the type of task.

For |CallFuture|, the |cancel| method either tells a waiting task
not to execute, or tells an already executing task that the user
is no longer interested in the result. It doesn't interrupt an
already executing background task.

For |IterationFuture|, the |cancel| method causes a running
background task to abort on the next iteration. No further results
are received after calling |cancel|.

For |ProgressFuture|, the |cancel| method causes a running
task to abort the next time that task calls ``progress``. No further
progress results are received after calling |cancel|.

In all cases, a future may only be cancelled if its state is one of |WAITING|
or |EXECUTING|. Attempting to cancel a future in another state will raise a
|RuntimeError|. Calling |cancel| immediately puts the future into
|CANCELLING| state, and the state is updated to |CANCELLED| once the future has
finished executing. No results or exception information are received from a
future in |CANCELLING| state. A cancelled future will never reach |FAILED|
state, and will never record information from a background task exception that
occurs after the |cancel| call.


Stopping the executor
---------------------

To avoid unexpected side-effects during Python process finalization, it's
recommended to shut down a running |TraitsExecutor| explicitly prior to process
exit. Similarly, when writing a unit test that makes use of a |TraitsExecutor|,
that executor should be shut down at test exit, to avoid potential for
unexpected interactions with other tests.

This section describes the two methods available for executor shutdown:
|shutdown| and |stop|.

Executor states
~~~~~~~~~~~~~~~

Like the various future classes, a |TraitsExecutor| also has a |executor_state|
trait, of type |ExecutorState|. This state is one of the following:

|RUNNING|
   The executor is running and accepting task submissions. This is the state
   of a newly-created executor.
|STOPPING|
   Shutdown has been initiated or partially completed, but there are still
   running background tasks associated with this executor. An executor in
   |STOPPING| state will not accept new task submissions.
|STOPPED|
   The executor has stopped, all resources associated with the executor have
   been released, and all background tasks associated with this executor have
   finished. An executor in |STOPPED| state will not accept new task
   submissions, and cannot be restarted.

Executor shutdown
~~~~~~~~~~~~~~~~~

Once a |TraitsExecutor| object is no longer needed (for example at application
shutdown time), it can be shut down via its |shutdown| method. This method is
blocking: it waits for all of the background tasks to complete before
returning. In more detail, if called on a running executor, the |shutdown|
method performs the following tasks, in order:

* Moves the executor to |STOPPING| state.
* Requests cancellation of all waiting or executing background tasks.
* Waits for all background tasks to complete.
* Shuts down the worker pool (if that worker pool is owned by the executor).
* Moves the executor to |STOPPED| state.

If called on an executor in |STOPPED| state, |shutdown| simply returns
without taking any action. If called on an executor in |STOPPING| state,
any of the above actions that have not already been taken will be taken.


Shutdown with a timeout
~~~~~~~~~~~~~~~~~~~~~~~

To avoid blocking indefinitely, the |shutdown| method also accepts a
``timeout`` parameter. That timeout is used when waiting for the background
tasks to complete. If the background tasks fail to complete within the given
timeout, |shutdown| will raise |RuntimeError| and leave the executor in
|STOPPING| state. The worker pool used by the executor will not have been shut
down.

Non-blocking executor shutdown
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Occasionally, it may be desirable to shut down an executor during normal
application execution, rather than at application shutdown time. In this
situation calling |shutdown| is problematic, since that method is blocking and
so will make the GUI unresponsive. Instead, users can call the non-blocking
|stop| method. This method:

* Moves the executor to |STOPPING| state.
* Requests cancellation of all waiting or executing background tasks.

Typically, the event loop will continue to run after calling the |stop| method.
Under that running event loop, all futures will eventually reach one of the
final states (|COMPLETED|, |FAILED| or |CANCELLED|). When that happens, the
system automatically:

* Shuts down the worker pool (if that worker pool is owned by the executor).
* Moves the executor to |STOPPED| state.

If there are no waiting or executing background tasks, then |stop| goes
through all of the steps above at once, moving the executor through
the |STOPPING| state to |STOPPED| state.

Note that while |stop| can only be called on an executor in |RUNNING| state,
it's always legal to call |shutdown| on an executor, regardless of the current
state of that executor. In particular, calling |shutdown| after |stop| is
permissible, but calling |stop| after |shutdown| would be an error.


Using a shared worker pool
--------------------------

By default, the |TraitsExecutor| creates its own worker pool, and shuts that
worker pool down when its |stop| method is called. In a large multithreaded
application, you might want to use a shared worker pool for multiple different
application components. In that case, you can instantiate the |TraitsExecutor|
with an existing worker pool, which should be an instance of
:class:`concurrent.futures.ThreadPoolExecutor`::

    worker_pool = concurrent.futures.ThreadPoolExecutor(max_workers=24)
    executor = TraitsExecutor(worker_pool=worker_pool)

It's then your responsibility to shut down the worker pool once it's no longer
needed.

..
   substitutions

.. |traits_futures| replace:: :mod:`traits_futures`
.. |traits_futures.api| replace:: :mod:`traits_futures.api`

.. |TraitsExecutor| replace:: :class:`~traits_futures.traits_executor.TraitsExecutor`
.. |shutdown| replace:: :meth:`~traits_futures.traits_executor.TraitsExecutor.shutdown`
.. |stop| replace:: :meth:`~traits_futures.traits_executor.TraitsExecutor.stop`

.. |executor_state| replace:: :attr:`~traits_futures.traits_executor.TraitsExecutor.state`
.. |ExecutorState| replace:: :data:`~traits_futures.executor_states.ExecutorState`
.. |RUNNING| replace:: :data:`~traits_futures.executor_states.RUNNING`
.. |STOPPING| replace:: :data:`~traits_futures.executor_states.STOPPING`
.. |STOPPED| replace:: :data:`~traits_futures.executor_states.STOPPED`

.. |cancel| replace:: :meth:`~traits_futures.i_future.IFuture.cancel`
.. |cancellable| replace:: :attr:`~traits_futures.i_future.IFuture.cancellable`
.. |done| replace:: :attr:`~traits_futures.i_future.IFuture.done`
.. |future_state| replace:: :attr:`~traits_futures.i_future.IFuture.state`
.. |result| replace:: :attr:`~traits_futures.i_future.IFuture.result`
.. |exception| replace:: :attr:`~traits_futures.i_future.IFuture.exception`

.. |CallFuture| replace:: :class:`~traits_futures.background_call.CallFuture`
.. |submit_call| replace:: :func:`~traits_futures.background_call.submit_call`

.. |IterationFuture| replace:: :class:`~traits_futures.background_iteration.IterationFuture`
.. |submit_iteration| replace:: :func:`~traits_futures.background_iteration.submit_iteration`
.. |result_event| replace:: :attr:`~traits_futures.background_iteration.IterationFuture.result_event`

.. |ProgressCancelled| replace:: :exc:`~traits_futures.background_progress.ProgressCancelled`
.. |ProgressFuture| replace:: :class:`~traits_futures.background_progress.ProgressFuture`
.. |submit_progress| replace:: :func:`~traits_futures.background_progress.submit_progress`
.. |progress| replace:: :attr:`~traits_futures.background_progress.ProgressFuture.progress`

.. |FutureState| replace:: :data:`~traits_futures.future_states.FutureState`
.. |WAITING| replace:: :data:`~traits_futures.future_states.WAITING`
.. |EXECUTING| replace:: :data:`~traits_futures.future_states.EXECUTING`
.. |COMPLETED| replace:: :data:`~traits_futures.future_states.COMPLETED`
.. |FAILED| replace:: :data:`~traits_futures.future_states.FAILED`
.. |CANCELLING| replace:: :data:`~traits_futures.future_states.CANCELLING`
.. |CANCELLED| replace:: :data:`~traits_futures.future_states.CANCELLED`

.. |Event| replace:: :class:`traits.trait_types.Event`

.. |AttributeError| replace:: :exc:`AttributeError`
.. |RuntimeError| replace:: :exc:`RuntimeError`
