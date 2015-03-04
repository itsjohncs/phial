__all__ = ("CommandQueue", )


class Command(object):
    def run(self, config):
        pass


class CommandQueue(object):
    def __init__(self):
        self._queue = []

    def enqueue(self, command):
        self._queue.append(command)

    def __iter__(self):
        return iter(self._queue)


global_queue = CommandQueue()
