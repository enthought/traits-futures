..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!


Threading carefully
===================

Traits Futures eliminates some potential threading-related pitfalls, but by no
means all of them. When using Traits Futures it's still important to have a
good understanding of general concurrency and threading-related issues
(deadlocks, race conditions, and so on). This section gives some
things to consider. Most of these recommendations are not specific to
Traits Futures, but apply more generally any time that you're writing
concurrent (and especially multithreaded) code.

-   **Never execute GUI code off the main thread.** With a few documented
    exceptions, most GUI objects should only ever be manipulated on the main
    thread. For example, a call to ``QLabel.setText`` that occurs on a worker
    thread may cause a crash or traceback, or may be completely fine until your
    application is deployed on a customer's machine. It's important to be aware
    that the Traits observation mechanisms together with the way that most
    TraitsUI editors work make it easy to *accidentally* make a change that
    triggers a GUI update from a worker thread.

-   **Avoid making blocking waits on the main thread.**
    To keep a running GUI responsive, avoid doing anything on the main thread
    that will block for more than a small amount of time (say 0.1 seconds).
    Where possible, set up your code to make asynchronous calls and react to
    the results of those calls, rather than making synchronous blocking calls
    on the main thread. In brief: reacting is preferable to polling; polling is
    preferable to blocking. (This is one of the key design principles behind
    Traits Futures.)

-   **Include a timeout in blocking calls.** If you're making
    a blocking wait call, consider including a timeout to avoid the possibility
    of that blocking wait blocking forever. If you're exposing potentially
    blocking calls to others in your own API, provide a timeout parameter that
    clients of your API can use. Having a timeout available is especially
    important for test suites, where you want to avoid the possibility of a
    single bad test hanging the entire test suite.

-   **Avoid writes to public traits on worker threads.** Public traits may have
    arbitrary listeners attached to them, and writes to those traits from a
    worker thread will trigger those listeners on the same thread, meaning that
    those listeners will have to be thread-safe. In general, people writing
    listeners for a public trait don't expect to have to make their listener
    thread-safe. Writing to a public trait from a worker thread is a
    common cause of making accidental GUI updates from a worker thread.

-   **Avoid reads from public traits on worker threads.** If there's any chance
    that a trait value might be modified while a background task is running,
    then that background task may run into race conditions. Instead of
    accessing a trait value on an object from a background task, consider
    retrieving the value at task submission time instead and passing it to the
    background task.

    Bad::

        class SomeView(HasStrictTraits):

            input = Int()

            def submit_background_task(self):
                future = submit_call(self.traits_executor, self.do_square)
                ...

            def do_square(self):
                # BAD: the return value might not even be a square, if the
                # value of self.input changes between the first attribute
                # access and the second.
                return self.input * self.input

    Better::

        class SomeView(HasStrictTraits):

            input = Int()

            def submit_background_task(self):
                future = submit_call(self.traits_executor, self.do_square)
                ...

            def do_square(self):
                # Only access self.input once, and cache and re-use the result
                # of that access.
                input = self.input
                return input * input

    Best::

        class SomeView(HasStrictTraits):

            input = Int()

            def submit_background_task(self):
                # Do the attribute access in the main thread; pass the result
                # of that access to the worker.
                future = submit_call(self.traits_executor, self.do_square, self.input)
                ...

            def do_square(self, input):
                return input*input

-   **Make copies of mutable data.** This is a generalization of the previous
    recommendation. If a background task depends on mutable data (for example,
    a dictionary of configuration values), it may make sense to make a private
    copy to pass to the background task. That way the background task doesn't
    have to worry about those data changing while it's running.

-   **Beware Traits defaults!** Idiomatic Traits-based code makes
    frequent use of lazy instantiation and defaults. For example, if your
    Traits class needed lock, you might consider writing code like this::

        class MyModel(HasStrictTraits):
            #: Some lock used to protect shared state.
            results_lock = Any()

            #: State shared by multiple threads
            results = Dict(Str, AnalysisResult)

            def _results_lock_default(self):
                return threading.Lock()

            def add_result(self, id, result):
                with self.results_lock:
                    results[id] = result

    But this is dangerous! The ``_results_lock_default`` method will be invoked
    lazily on first use, and can be invoked simultaneously (or
    near-simultaneously) on two different threads. We then temporarily have two
    different locks, allowing ``results`` to be simultaneously accessed from
    multiple threads and defeating the point of the lock.

    In this case, it's better to create the ``results_lock`` explicitly in the
    main thread when ``MyModel`` is instantiated (e.g., by adding an
    ``__init__`` method). Better still, rework the design to avoid needing to
    share ``results`` between multiple threads in the first place.

-   **Have a clear, documented thread-ownership model.** The organization and
    documentation of your code should make it clear which pieces of code are
    intended for possible execution by a worker thread, which pieces of code
    might be executed simultaneously by multiple threads, and which pieces of
    code are required to be thread-safe. Ideally, the portion of the codebase
    that needs to be thread-safe should be small, isolated, and clearly
    identifiable. (Writing, reasoning about, maintaining and testing
    thread-safe code is difficult and error-prone. We want to do as little of
    it as we possibly can.)

-   **Keep task-coordination logic in the main thread.** Sometimes you want to
    execute additional tasks depending on the results of an earlier task. In
    that case it may be tempting to try to launch those additional tasks
    directly within the code for the earlier task, but the logic is likely to
    be more manageable if it's all kept in the main thread: fire off the first
    task, then add a trait listener for its completion that inspects the
    results and fires off additional tasks as necessary. Traits Futures
    currently encourages this model by forbidding submission of new tasks from
    a background thread, though that restriction may be lifted in the future.

-   **Avoid having too many Python threads.** Python 3's GIL logic can have
    limiting effects when there are too many Python threads, in some cases
    causing non-CPU-bound threads not to have a chance to run at all. Avoid
    creating too many Python threads in your process. The reasonable upper
    bound will be context dependent, but as a rule of thumb, if you have more
    than 20 Python threads, consider whether there's a way of reducing the
    total number.

-   **Always join your threads.** At application shutdown time, or on exit from
    a script, or in a test's ``tearDown`` method, explicitly join any threads
    that you created directly. Similarly, explicitly shut down worker pools and
    executors. Clean shutdown helps to avoid odd side-effects at Python process
    exit time, and to avoid hard-to-debug interactions between tests in a test
    suite.

-   **Use thread pools.** Use thread pools in preference to creating your own
    worker threads. This makes it easy to shut down worker threads, and to
    avoid an explosion of Python threads (see the last two items).
