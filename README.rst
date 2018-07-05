traits-futures
--------------

The traits-futures library demonstrates robust design patterns for reactive
background jobs triggered from a Traits UI application.

Motivating example
------------------
A customer has asked you to wrap their black-box optimization code in a GUI.

You build a simple Traits UI GUI that allows the user to set inputs and options
and then press the big green "Calculate" button. The requirements look something
like this:

- The UI should remain usable and responsive while the background calculation
  is running.
- The UI should update (e.g., show a plot, or show results) in response to the 
  background calculation completing normally.
- The background job should be cancellable.
- The UI should react appropriately if the background job raises an exception.

And there are some further ease-of-development requirements:

- As far as possible, the UI developer shouldn't have to think about managing
  the background threads or re-dispatching incoming information from the
  background task(s). The UI developer should be able to simply listen to and
  react to suitable traits for information coming in from the background task.
- It should be possible to switch between using background threads and
  background process (and possibly also coroutines) with minimal effort.

Getting started
---------------
Note: build infrastructure for this repository is in progress, and these
instructions will become less vague and easier to use once it's complete.

There's an example Traits UI application in ``traits_futures.example``. After
setting up a suitable development environment, you can run the example with:

    python -m traits_futures.example

Now look at the ``example.py`` source code and note how straightforward it is:
Traits listeners, but no explicit threads or locks in sight.

