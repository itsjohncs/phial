__all__ = ["CommandQueue"]


class Command(object):
    def run(self, config):
        pass


class CommandQueue(object):
    def __init__(self):
        self._queue = []

    def enqueue(self, command):
        self._queue.append(command)

    def __iter__(self):
    	# Note that this sort is stable
        sorted_queue = sorted(self._queue, key=lambda x: getattr(x, "priority", 0))
        return iter(sorted_queue)


global_queue = CommandQueue()
