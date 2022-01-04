..
   (C) Copyright 2018-2022 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!

Advanced topics
===============

.. note::
   Support for writing custom tasks is provisional. The API is subject to
   change in future releases. Feedback on the feature is welcome.


Creating your own background task type
--------------------------------------

Traits Futures comes with three basic background task types: background calls,
background iterations and background progress calls, created via the
|submit_call|, |submit_iteration| and |submit_progress| functions,
respectively. In each case, communication from the background task to the
corresponding foreground |IFuture| instance is implemented by sending custom
task-type-specific messages of the form ``(message_type, message_value)``,
where ``message_type`` is a suitable string describing the type of the message.
For example, the progress task sends messages of type ``"progress"`` to report
progress, while the background iteration task sends messages of type
``"generated"``.

If none of the standard task types meets your needs, it's possible to write
your own background task type, that sends whatever messages you like. Two base
classes, |BaseFuture| and |BaseTask|, are made available to make this easier.
This section describes how to do this in detail.

To create your own task type, you'll need three ingredients:

- A factory for the background callable.
- A suitable future type, implementing the |IFuture| interface.
- A *task specification* class, implementing the |ITaskSpecification|
  interface. The |submit| method of the TraitsExecutor expects an instance of
  |ITaskSpecification|, and interrogates that instance to get the background
  callable and the corresponding foreground future.

You may optionally also want to create a convenience function analogous to the
existing |submit_call|, |submit_iteration| and |submit_progress| functions.

Below we give a worked example that demonstrates how to create each of these
ingredients for a simple case.

Worked example: Fizz buzz!
--------------------------

In this section we'll create an example new background task type, based on the
well-known `Fizz buzz <fizz_buzz_>`_ game. We'll create a background task that
counts slowly from 1, sending three different types of messages to the
foreground: it sends "Fizz" messages on multiples of 3, "Buzz" messages on
multiples of 5, and "Fizz Buzz" messages on multiples of 15. Each message
is accompanied by the corresponding number.

Message types
~~~~~~~~~~~~~

In general, each message sent from the background task to the future can be any
Python object, and the future can interpret the sent object in any way that it
likes. However, the |BaseFuture| and |BaseTask| convenience base classes that
we'll use below provide helper functions to handle and dispatch messages of
the form ``(message_type, message_args)``. Here the message type should be
a string that's valid as a Python identifier, while the message argument can be
any Python object (though it should usually be pickleable and immutable).

We first define named constants representing our three message types. This
isn't strictly necessary, but it makes the code cleaner.

.. literalinclude:: examples/fizz_buzz_task.py
    :start-after: start message types
    :end-before: end message types

The background callable
~~~~~~~~~~~~~~~~~~~~~~~

Next, we define the callable that will be run in the background. The callable
itself expects two arguments (which will be passed by position): ``send`` and
``cancelled``. The ``send`` object is a callable which will be used to send
messages to the foreground. The ``cancelled`` object is a zero-argument
callable which can be used to check for cancellation requests.

However, instead of implementing this callable directly, we inherit from the
|BaseTask| abstract base class. This requires us to implement a (parameterless)
|run| method for the body of the task. The |run| method has access to methods
|send| and |cancelled| to send messages to the associated |BaseFuture| instance
and to check whether the user has requested cancellation.

Here's the ``fizz_buzz`` callable.

.. literalinclude:: examples/fizz_buzz_task.py
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
background task are processed by the |dispatch| method. The default
implementation of this method expects incoming messages to have the form
``(message_type, message_arg)``, and it converts each such message to a call to
a method named ``_process_<message_type>``, passing ``message_arg`` as an
argument.

The |dispatch| method can be safely overridden by subclasses if messages
do not have the form ``(message_type, message_arg)``, or if some
other dispatch mechanism is wanted. For this example, we use the default
dispatch mechanism, so all we need to do is to define methods
``_process_fizz``, ``_process_buzz`` and ``_process_fizz_buzz`` to handle
messages of types ``FIZZ``, ``BUZZ`` and ``FIZZ_BUZZ`` respectively. We choose
to process each message by firing a corresponding event on the future.

.. literalinclude:: examples/fizz_buzz_task.py
    :start-after: start FizzBuzzFuture
    :end-before: end FizzBuzzFuture

Putting it all together: the task specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The last piece we need is a task specification, which is the object that can be
submitted to the |TraitsExecutor|. This object needs to have two attributes:
``future`` and ``task``. Given an instance ``task`` of a task
specification, the |TraitsExecutor| calls ``task.future(cancel)``
to create the future, and ``task.task()`` to create the background
callable. For the background task, we want to return (but not call!) the
``fizz_buzz`` function that we defined above. For the future, we create and
return a new ``FizzBuzzFuture`` instance. So our task specification
looks like this:

.. literalinclude:: examples/fizz_buzz_task.py
    :start-after: start BackgroundFizzBuzz
    :end-before: end BackgroundFizzBuzz

Submitting the new task
~~~~~~~~~~~~~~~~~~~~~~~

With all of the above in place, a Fizz buzz background task can be submitted to
a |TraitsExecutor| ``executor`` by passing an instance of
``BackgroundFizzBuzz`` to ``executor.submit``. For convenience, we can
encapsulate that operation in a function:

.. literalinclude:: examples/fizz_buzz_task.py
    :start-after: start submit_fizz_buzz
    :end-before: end submit_fizz_buzz

An example GUI
~~~~~~~~~~~~~~

Here's the :download:`complete script <examples/fizz_buzz_task.py>` obtained
from putting together the above snippets:

.. literalinclude:: examples/fizz_buzz_task.py
   :start-after: Thanks for using Enthought
   :lines: 2-

And here's an :download:`example GUI <examples/fizz_buzz_ui.py>` that makes use
of the new background task type:

.. literalinclude:: examples/fizz_buzz_ui.py
   :start-after: Thanks for using Enthought
   :lines: 2-


..
   external links

.. _fizz_buzz: https://en.wikipedia.org/wiki/Fizz_buzz

..
   substitutions

.. |BaseFuture| replace:: :class:`~.BaseFuture`
.. |BaseTask| replace:: :class:`~.BaseTask`
.. |cancelled| replace:: :meth:`~.BaseTask.cancelled`
.. |dispatch| replace:: :meth:`~.BaseFuture.dispatch`
.. |exception| replace:: :attr:`~traits_futures.base_future.BaseFuture.exception`
.. |HasStrictTraits| replace:: :class:`~traits.has_traits.HasStrictTraits`
.. |IFuture| replace:: :class:`~.IFuture`
.. |ITaskSpecification| replace:: :class:`~.ITaskSpecification`
.. |result| replace:: :attr:`~traits_futures.base_future.BaseFuture.result`
.. |run| replace:: :meth:`~.BaseTask.run`
.. |send| replace:: :meth:`~.BaseTask.send`
.. |submit| replace:: :meth:`~.submit`
.. |submit_call| replace:: :func:`~.submit_call`
.. |submit_iteration| replace:: :func:`~.submit_iteration`
.. |submit_progress| replace:: :func:`~.submit_progress`
.. |TraitsExecutor| replace:: :class:`~.TraitsExecutor`
