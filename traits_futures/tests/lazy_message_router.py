from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools

from six.moves import queue

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int


class LazyMessageSender(object):
    def __init__(self, sender_id, message_queue):
        self.sender_id = sender_id
        self.message_queue = message_queue

    def __enter__(self):
        pass

    def __exit__(self, *exc_info):
        self.message_queue.put(("done", self.sender_id))

    def send(self, message):
        self.message_queue.put(("message", self.sender_id, message))


class LazyMessageReceiver(HasStrictTraits):
    #: Event fired when a message is received from the paired sender.
    message = Event(Any)


class LazyMessageRouter(HasStrictTraits):
    #: Internal queue for messages from workers.
    _message_queue = Any

    #: Source of task ids for new tasks.
    _sender_ids = Instance(collections.Iterator)

    #: Receivers, keyed by sender_id.
    _receivers = Dict(Int, Any)

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
        self._receivers[sender_id] = receiver
        return sender, receiver

    def _read_message(self):
        wrapped_message = self._message_queue.get()
        if wrapped_message[0] == "message":
            _, sender_id, message = wrapped_message
            receiver = self._receivers[sender_id]
            receiver.message = message
        else:
            assert wrapped_message[0] == "done"
            _, sender_id = wrapped_message
            del self._receivers[sender_id]

    def send_until(self, condition, timeout):
        while not condition():
            self._read_message()
