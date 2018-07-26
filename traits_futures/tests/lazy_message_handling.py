from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools

from six.moves import queue

from traits.api import Any, Event, HasStrictTraits, Instance, Int, Tuple


class LazyMessageSender(object):
    def __init__(self, sender_id, message_queue):
        self.sender_id = sender_id
        self.message_queue = message_queue

    def __enter__(self):
        pass

    def __exit__(self, *exc_info):
        pass

    def send(self, message):
        self.message_queue.put((self.sender_id, message))


class LazyMessageReceiver(HasStrictTraits):
    #: Event fired when a message is received from the paired sender.
    message = Event(Any)


class LazyMessageRouter(HasStrictTraits):
    #: Event fired whenever a message is received. The first part of
    #: the received message is the sender id. The second part is
    #: the message itself.
    received = Event(Tuple(Int, Any))

    #: Internal queue for messages from workers.
    _message_queue = Any

    #: Source of task ids for new tasks.
    _sender_ids = Instance(collections.Iterator)

    def __message_queue_default(self):
        return queue.Queue()

    def __sender_ids_default(self):
        return itertools.count()

    def sender(self):
        """
        Create a new LazyMessageSender for this router.
        """
        sender_id = next(self._sender_ids)
        sender = LazyMessageSender(
            sender_id=sender_id,
            message_queue=self._message_queue,
        )
        receiver = LazyMessageReceiver()
        return sender_id, sender, receiver

    def send_until(self, condition, timeout):
        while not condition():
            message = self._message_queue.get(timeout=timeout)
            self.received = message
