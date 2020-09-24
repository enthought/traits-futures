..
   (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
   All rights reserved.

User guide
==========

In this guide we'll introduce the key players in the |traits_futures|
package. All classes and data items mentioned here can be imported directly
from the |traits_futures.api| module.

Submitting background tasks
---------------------------

The |TraitsExecutor| is the main point of entry to |traits_futures|. Its job is
to accept one or more task submissions. For each task submitted, it sends the
computation to run in the background on a thread pool worker, and returns a
corresponding "future" object that allows monitoring of the state of the
background computation and retrieval of its results.

We'll examine the future objects in the next section. This section deals with
the executor's main top-level methods.

To submit a task, use one of the |TraitsExecutor| top-level methods:

- The |submit_call| method allows submission of a simple Python callable, with
  given positional and named arguments. For example::

    my_executor.submit_call(int, "10101", base=2)

  will execute ``int("10101", base=2)`` in the background. |submit_call|
  doesn't wait for the background task to finish; instead, it immediately
  returns a |CallFuture| object. See the next section for more details on
  the |CallFuture| and related objects.

- The |submit_iteration| method allows submission of an arbitrary iterable. The
  user provides a callable which, when called, returns an iterable object. For
  example::

    my_executor.submit_iteration(range, 0, 5)

  It returns a |IterationFuture| object.

- The |submit_progress| method allows submission of a progress-reporting
  callable, and returns a |ProgressFuture| object. The callable submitted
  *must* have a parameter called "progress".  A value for this parameter will
  be passed (by name) by the executor machinery. The value passed for the
  "progress" parameter can then be called to send progress reports to the
  associated |ProgressFuture| object.

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
  compound object like a ``tuple`` or a ``dict``. It's up to you to choose the
  format of the objects you want to send. They'll arrive in exactly the same
  format in the |ProgressFuture|, and then your application can choose how to
  interpret them.


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
``state`` trait, of trait type |FutureState|, that represents the state of the
underlying computation. That state has one of six possible different values:

|WAITING|
   The background task has been scheduled to run, but has not yet started
   executing (for example, because the thread pool is still busy dealing
   with previously-submitted tasks.

|EXECUTING|
   The background task is currently executing on one of the thread pool
   workers.

|COMPLETED|
   The background task has completed without error. For a progress task or a
   simple call, this implies that a result has been returned and is available
   via the ``result`` property of the future. For an iteration, it means that
   the iteration has completed.

|FAILED|
   The background task raised an exception at some point in its execution.
   Information about the exception is available via the ``exception`` property
   of the future.

|CANCELLING|
   Cancellation of the background task has been requested, but the background
   task has not yet acknowledged that request.

|CANCELLED|
   The task has stopped following a cancellation request.

In addition, there are two traits whose values are derived from the ``state``
trait: the ``done`` trait is ``True`` when ``state`` is one of |COMPLETED|,
|FAILED| or |CANCELLED|, and the ``cancellable`` trait is ``True`` when
``state`` is one of |WAITING| or |EXECUTING|.

It's important to understand that the ``state`` trait represents the state of
the background task *to the best of knowledge* of the main thread. For example,
when the background task starts executing, it sends a message to the
corresponding future telling it to change its state from |WAITING| to
|EXECUTING|. However, that message won't necessarily get processed immediately,
so there will be a brief interval during which the background task has, in
fact, started executing, but the state of the future is still |WAITING|.


Getting task results
~~~~~~~~~~~~~~~~~~~~

Background task results can be retrieved directly from the corresponding
futures.

The |submit_call| and |submit_progress| methods run callables that eventually
expect to return a result. Once the state of the corresponding future reaches
|COMPLETED|, the result of the call is available via the ``result`` attribute.
Assuming that your calculation future is stored in a trait called ``future``,
you might use this as follows::

    @on_trait_change('future:done')
    def _update_result(self, future, name, done):
        self.my_results.append(future.result)

Any attempt to access ``future.result`` before the future completes
successfully raises an ``AttributeError``. This includes the cases where
the background task was cancelled, or failed with an exception, as well
as the cases where the task is still executing or has yet to start running.

A |ProgressFuture| object also receives progress information send by the
background task via its ``progress`` event trait. You might use that
trait like this::

    @on_trait_change('future:progress')
    def _report_progress(self, progress_info):
        current_step, max_steps, matches = progress_info
        self.message = "{} of {} chunks processed. {} matches so far".format(
            current_step, max_steps, matches)

The |submit_iteration| method is a little bit different: it produces a result
on each iteration, but doesn't give any final result. Its ``result_event``
trait is an ``Event`` that you can hook listeners up to in order to receive the
results. For example::

    @on_trait_change('future:result_event')
    def _record_result(self, result):
        self.results.append(result)
        self.update_plot_data()

If a background task fails with an exception, then the corresponding
future ``future`` eventually reaches |FAILED| state. In that case,
information about the exception that occurred is available in the
``future.exception`` attribute. This information takes the form of
a ``tuple`` of length 3, containing stringified versions of the
exception type, the exception value and the exception traceback.

As with ``future.result``, an attempt to access ``future.exception`` for a
``future`` that's not in |FAILED| state will give an ``AttributeError``.


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
``RuntimeError``. Calling |cancel| immediately puts the future into
|CANCELLING| state, and the state is updated to |CANCELLED| once the future has
finished executing. No results or exception information are received from a
future in |CANCELLING| state. A cancelled future will never reach |FAILED|
state, and will never record information from a background task exception that
occurs after the |cancel| call.


Stopping the executor
---------------------

Like the various future classes, a |TraitsExecutor| also has a state trait, of
type |ExecutorState|. This state is one of the following:

|RUNNING|
   The executor is running and accepting task submissions.
|STOPPING|
   The user has requested that the executor stop, but there are still
   running futures associated with this executor. An executor in |STOPPING|
   state will not accept new task submissions.
|STOPPED|
   The executor has stopped, and all futures associated with this
   executor have finished. An executor in this state cannot be
   used to submit new tasks, and cannot be restarted.

Once a |TraitsExecutor| object is no longer needed (for example at application
shutdown time), its |stop| method may be called. This cancels all current
executing or waiting futures, puts the executor into |STOPPING| state and then
returns.

Once all futures reach |CANCELLED| state, an executor in |STOPPING| state moves
into |STOPPED| state. If the executor owns its thread pool, that thread pool is
shut down immediately before moving into |STOPPED| state.

It's advisable to stop the executor explicitly and wait for it to reach
|STOPPING| state before exiting an application using it.


Using a shared thread pool
--------------------------

By default, the |TraitsExecutor| creates its own thread pool, and shuts that
thread pool down when its |stop| method is called. In a large multithreaded
application, you might want to use a shared thread pool for multiple different
application components. In that case, you can instantiate the |TraitsExecutor|
with an existing thread pool, which should be an instance of
``concurrent.futures.ThreadPoolExecutor``::

    thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=24)
    executor = TraitsExecutor(thread_pool=thread_pool)

It's then your responsibility to shut down the thread pool once it's no longer
needed.

..
   substitutions

.. |traits_futures| replace:: :mod:`traits_futures`
.. |traits_futures.api| replace:: :mod:`traits_futures.api`

.. |TraitsExecutor| replace:: :class:`~traits_futures.traits_executor.TraitsExecutor`
.. |submit_call| replace:: :meth:`~traits_futures.traits_executor.TraitsExecutor.submit_call`
.. |submit_iteration| replace:: :meth:`~traits_futures.traits_executor.TraitsExecutor.submit_iteration`
.. |submit_progress| replace:: :meth:`~traits_futures.traits_executor.TraitsExecutor.submit_progress`
.. |stop| replace:: :meth:`~traits_futures.traits_executor.TraitsExecutor.stop`

.. |ExecutorState| replace:: :meth:`~traits_futures.traits_executor.ExecutorState`
.. |RUNNING| replace:: :meth:`~traits_futures.traits_executor.RUNNING`
.. |STOPPING| replace:: :meth:`~traits_futures.traits_executor.STOPPING`
.. |STOPPED| replace:: :meth:`~traits_futures.traits_executor.STOPPED`

.. |CallFuture| replace:: :class:`~traits_futures.background_call.CallFuture`
.. |IterationFuture| replace:: :class:`~traits_futures.background_iteration.IterationFuture`
.. |ProgressFuture| replace:: :class:`~traits_futures.background_progress.ProgressFuture`

.. |cancel| replace:: :class:`~traits_futures.background_call.CallFuture.cancel`

.. |FutureState| replace:: :data:`~traits_futures.future_states.FutureState`
.. |WAITING| replace:: :data:`~traits_futures.future_states.WAITING`
.. |EXECUTING| replace:: :data:`~traits_futures.future_states.EXECUTING`
.. |COMPLETED| replace:: :data:`~traits_futures.future_states.COMPLETED`
.. |FAILED| replace:: :data:`~traits_futures.future_states.FAILED`
.. |CANCELLING| replace:: :data:`~traits_futures.future_states.CANCELLING`
.. |CANCELLED| replace:: :data:`~traits_futures.future_states.CANCELLED`
