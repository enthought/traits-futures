..
   (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
   All rights reserved.

Advanced topics
===============

Creating your own background task type
--------------------------------------

Traits Futures comes with three basic background task types: background calls,
background iterations and background progress calls, created via the
|submit_call|, |submit_iteration| and |submit_progress| functions,
respectively. In each case, communication from the background task to the
corresponding foreground |IFuture| instance is implemented by sending
custom task-type-specific messages, with the type of message identified by
a suitable string. For example, the background progress task sends messages
of type ``"progress"`` to report progress, while the background iteration task
sends messages of type ``"generated"``.

If none of the standard task types meets your needs, it's possible to write
your own background task type, that sends whatever message types you like. This
section describes how to do this in detail.

To create your own task type, you'll need three ingredients:

- A factory for the background callable.
- A suitable future type, implementing the |IFuture| interface.
- A *task specification* class, implementing the |ITaskSpecification|
  interface. The |submit| method of the TraitsExecutor expects an instance of
  |ITaskSpecification|, and interrogates that instance to get the background
  callable and the corresponding foreground future.

Below we give a worked example that demonstrates how to create each of these
ingredients for a simple case.

Worked example: Fizz buzz!
--------------------------

In this section we'll create an example new background task type, based on the
well-known `Fizz buzz <fizzbuzz>`_ game. We'll create a background task that
counts slowly from 1, sending messages to the foreground on multiples of 3, 5
and 15.

In general, a message sent from the background to the foreground has two parts:
a message type, and an optional message argument. The message type should be a
string, while the message argument can be any Python object (though it should
usually be pickleable and immutable).

Message types
~~~~~~~~~~~~~

We'll define three message types: one for FIZZ messages, one for BUZZ messages
and one for FIZZ BUZZ messages.

.. literalinclude:: examples/fizzbuzz_task.py
    :start-after: start message types
    :end-before: end message types

Note that the message types are all strings. Ideally, those strings should be
valid Python identifiers, since (as we'll see later) the default message
dispatch mechanism uses these strings directly in the corresponding message
handler names.

The background callable
~~~~~~~~~~~~~~~~~~~~~~~

Next, we define the callable that will be run in the background. This callable
must accept two arguments (which will be passed by position): ``send`` and
``cancelled``. The ``send`` object is a callable which will be used to send
messages to the foreground. The ``cancelled`` object is a zero-argument
callable which can be used to check for cancellation requests. Here's the
``fizz_buzz`` callable.

.. literalinclude:: examples/fizzbuzz_task.py
    :start-after: start fizz_buzz
    :end-before: end fizz_buzz

In this example, we don't return anything from the ``fizz_buzz`` function, but
in general any object returned by the background callable will be made
available under the |result| property of the corresponding future. Similarly,
any exception raised during execution will be made available under the
|exception| property of the corresponding future.

The foreground Future
~~~~~~~~~~~~~~~~~~~~~

Now we define a dedicated future class ``FizzBuzzFuture`` for this background
task type. The most convenient way to do this is to inherit from the
|BaseFuture| class, which is a |HasStrictTraits| subclass that provides the
|IFuture| interface. Messages coming into the |BaseFuture| instance from the
background task are processed by the |dispatch_message| method. The default
implementation of this method does a couple of things:

- it dispatches the argument of each message to a method named
  ``_process_<message_type>``.
- it suppresses any messages that arrive after cancellation has been requested

The |dispatch_message| method can be safely overridden by subclasses if some
other dispatch mechanism is wanted. For this example, we use the default
dispatch mechanism, so all we need to do is to define methods
``_process_fizz``, ``_process_buzz`` and ``_process_fizz_buzz`` to handle
messages of types ``FIZZ``, ``BUZZ`` and ``FIZZ_BUZZ`` respectively. We choose
to process each message by firing a corresponding event on the future.

.. literalinclude:: examples/fizzbuzz_task.py
    :start-after: start FizzBuzzFuture
    :end-before: end FizzBuzzFuture

Putting it all together: the task specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The last piece we need is a task specification, which is the object that can be
submitted to the |TraitsExecutor|. This object needs to have two attributes:
``future`` and ``background_task``. Given an instance ``task`` of a task
specification, the |TraitsExecutor| calls ``task.future(_cancel=cancel_event)``
to create the future, and ``task.background_task()`` to create the background
callable. So our task specification simply looks like this:

.. literalinclude:: examples/fizzbuzz_task.py
    :start-after: start BackgroundFizzBuzz
    :end-before: end BackgroundFizzBuzz


With all of the above in place, a Fizz buzz background task can be submitted
to a |TraitsExecutor| simply by doing:

.. code-block:: python

    task = BackgroundFizzBuzz()
    future = executor.submit(task)

Putting everything together, here's the complete code:

.. literalinclude:: examples/fizzbuzz_task.py

And here's an example GUI that makes use of the new background task type:

.. literalinclude:: examples/fizzbuzz_ui.py


..
   external links

.. _fizzbuzz: https://en.wikipedia.org/wiki/Fizz_buzz


..
   substitutions

.. |BaseFuture| replace:: :class:`~.BaseFuture`
.. |dispatch_message| replace:: :meth:`~.BaseFuture.dispatch_message`
.. |exception| replace:: :attr:`~traits_futures.i_future.IFuture.exception`
.. |HasStrictTraits| replace:: :class:`~traits.has_traits.HasStrictTraits`
.. |IFuture| replace:: :class:`~.IFuture`
.. |ITaskSpecification| replace:: :class:`~.ITaskSpecification`
.. |result| replace:: :attr:`~traits_futures.i_future.IFuture.result`
.. |submit| replace:: :meth:`~.submit`
.. |submit_call| replace:: :func:`~.submit_call`
.. |submit_iteration| replace:: :func:`~.submit_iteration`
.. |submit_progress| replace:: :func:`~.submit_progress`
.. |TraitsExecutor| replace:: :class:`~.TraitsExecutor`
