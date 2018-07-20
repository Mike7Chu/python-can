#!/usr/bin/env python
# coding: utf-8

"""
This module contains the implementation of `can.Listener` and some readers.
"""

from abc import ABCMeta, abstractmethod

try:
    # Python 3.7
    from queue import SimpleQueue, Empty
except ImportError:
    try:
        # Python 3.0 - 3.6
        from queue import Queue as SimpleQueue, Empty
    except ImportError:
        # Python 2
        from Queue import Queue as SimpleQueue, Empty


class Listener(object):
    """The basic listener that can be called directly to handle some
    CAN message::

        listener = SomeListener()
        msg = my_bus.recv()

        # now either call
        listener(msg)
        # or
        listener.on_message_received(msg)

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def on_message_received(self, msg):
        """This method is called to handle the given message.

        :param can.Message msg: the delivered message

        """
        pass

    def __call__(self, msg):
        return self.on_message_received(msg)

    def stop(self):
        """
        Override to cleanup any open resources.
        """


class RedirectReader(Listener):
    """
    A RedirectReader sends all received messages to another Bus.

    """

    def __init__(self, bus):
        self.bus = bus

    def on_message_received(self, msg):
        self.bus.send(msg)


class BufferedReader(Listener):
    """
    A BufferedReader is a subclass of :class:`~can.Listener` which implements a
    **message buffer**: that is, when the :class:`can.BufferedReader` instance is
    notified of a new message it pushes it into a queue of messages waiting to
    be serviced. The messages can then be fetched with
    :meth:`~can.BufferedReader.get_message`.

    Putting in messages after :meth:`~can.BufferedReader.stop` has be called will raise
    an exception, see :meth:`~can.BufferedReader.on_message_received`.

    :attr bool is_stopped: ``True`` iff the reader has been stopped
    """

    def __init__(self):
        # 0 is "infinite" size
        self.buffer = SimpleQueue(0)

    def on_message_received(self, msg):
        """Append a message to the buffer.

        :raises: BufferError
            if the reader has already been stopped
        """
        if self.is_stopped:
            raise BufferError("reader has already been stopped")
        else:
            self.buffer.put(msg)

    def get_message(self, timeout=0.5):
        """
        Attempts to retrieve the latest message received by the instance. If no message is
        available it blocks for given timeout or until a message is received, or else
        returns None (whichever is shorter). This method does not block after
        :meth:`can.BufferedReader.stop` has been called.

        :param float timeout: The number of seconds to wait for a new message.
        :rytpe: can.Message or None
        :return: the message if there is one, or None if there is not.
        """
        try:
            return self.buffer.get(block=not self.is_stopped, timeout=timeout)
        except Empty:
            return None

    def stop(self):
        """Prohibits any more additions to this reader.
        """
        self.is_stopped = True
