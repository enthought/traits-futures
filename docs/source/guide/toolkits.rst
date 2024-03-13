..
   (C) Copyright 2018-2024 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!

Toolkits and running headless
=============================

Each |TraitsExecutor| requires a running event loop to communicate results from
background tasks to the foreground. In a typical GUI application, that event
loop will be the event loop from the current GUI toolkit - for example Qt or
Wx. However, one can also use the main thread |asyncio| event loop from
Python's standard library. This is potentially useful when writing automated
tests, or when using Traits Futures in a headless setting (for example within
a compute job).

Specifying a toolkit
--------------------

To explicitly specify which toolkit to use, you need to provide the
``event_loop`` parameter when instantiating the |TraitsExecutor|. The library
currently provides four different event loops: |AsyncioEventLoop|,
|QtEventLoop|, |WxEventLoop| and |ETSEventLoop|.

By default, if no event loop is explicitly specified, an instance of
|ETSEventLoop| is used. This follows the usual ETS rules to determine which
toolkit to use based on the value of the ``ETS_TOOLKIT`` environment variable,
on whether any other part of the ETS machinery has already "fixed" the toolkit,
and on which toolkits are available in the current Python environment.

Running Traits Futures in a headless setting
--------------------------------------------

In general, if you're writing code that's not GUI-oriented, you
probably don't want to be using Traits Futures at all: the library is
explicitly designed for working in a GUI-based setting, in situations where you
don't want your computational or other tasks to block the GUI event loop and
generate the impression of an unresponsive GUI. Instead, you might execute
your tasks directly in the main thread or, if you need to take advantage
of thread-based parallelism, use the |concurrent.futures| framework
directly.

However, you may find yourself in a situation where you already have Traits
Futures-based code that was written for a GUI setting, but that you want to be
able to execute in a environment that doesn't have the Qt or Wx toolkits
available. In that case, Traits Futures can use the |AsyncioEventLoop| to
deliver results to the main thread's |asyncio| event loop instead of to
a GUI framework's event loop.

Here's an :download:`example script <examples/headless.py>` that uses the
|AsyncioEventLoop| in order to execute Traits Futures tasks within the context
of an asyncio event loop.

.. literalinclude:: examples/headless.py
   :start-after: Thanks for using Enthought
   :lines: 2-

..
   substitutions


.. |asyncio| replace:: :mod:`asyncio`
.. |concurrent.futures| replace:: :mod:`concurrent.futures`
.. |AsyncioEventLoop| replace:: :class:`~.AsyncioEventLoop`
.. |ETSEventLoop| replace:: :class:`~.ETSEventLoop`
.. |QtEventLoop| replace:: :class:`~.QtEventLoop`
.. |WxEventLoop| replace:: :class:`~.WxEventLoop`
.. |TraitsExecutor| replace:: :class:`~.TraitsExecutor`
