..
   (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
   All rights reserved.

   This software is provided without warranty under the terms of the BSD
   license included in LICENSE.txt and may be redistributed only under
   the conditions described in the aforementioned license. The license
   is also available online at http://www.enthought.com/licenses/BSD.txt

   Thanks for using Enthought open source!

Toolkits and running headless
=============================

The |TraitsExecutor| requires a running event loop to communicate results from
background tasks to the foreground. In a typical GUI application, that event
loop will be the event loop from the current GUI toolkit - for example Qt or
Wx. However, one can also use the main thread |asyncio| event loop from
Python's standard library. This is potentially useful when writing automated
tests, and when using Traits Futures in a headless setting (for example within
a compute job).

To explicitly specify which toolkit to use, you need to provide the
``gui_context`` parameter when instantiating the |TraitsExecutor|. The library
currently provides four different GUI contexts: |AsyncioContext|, |QtContext|,
|WxContext| and |ETSContext|.  The first three correspond to the |asyncio|
event loop, the Qt event loop and the Wx event loop respectively.

By default, if no gui context is explicitly specified, an instance of
|ETSContext| is used. This follows the usual ETS rules to determine which
toolkit to use based on the value of the ``ETS_TOOLKIT`` environment variable,
on whether any other part of the ETS machinery has already "fixed" the toolkit,
and on which toolkits are available in the current Python environment.





..
   substitutions


.. |asyncio| replace:: :mod:`asyncio`
.. |AsyncioContext| replace:: :class:`~.AsyncioContext`
.. |ETSContext| replace:: :class:`~.ETSContext`
.. |QtContext| replace:: :class:`~.QtContext`
.. |WxContext| replace:: :class:`~.WxContext`
.. |TraitsExecutor| replace:: :class:`~.TraitsExecutor`
