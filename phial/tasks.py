# internal
from . import utils


@utils.public
class Task(object):
    def run(self, config):
        pass


@utils.public
class TaskQueue(object):
    def __init__(self):
        self._queue = []

    def enqueue(self, task):
        self._queue.append(task)

    def __iter__(self):
        return iter(self._queue)


global_queue = TaskQueue()
__all__.append("global_queue")  # noqa
