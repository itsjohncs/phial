# internal
from . import utils


@utils.public
class Task(object):
    def __init__(self, id, depends_on=None):
        self.id = id
        self.depends_on = depends_on

    def get_dependencies(self):
        if self.depends_on is None:
            return []
        elif isinstance(self.depends_on, list):
            return self.depends_on

        return [self.depends_on]

    def run(self, config):
        pass


@utils.public
class TaskQueue(object):
    def __init__(self):
        self._queue = []

    def _get_topologically_sorted_queue(self):
        # Will hold the resulting list
        result = []

        # The tasks added to the list already
        visited = set()

        # Tasks that we've visited in the latest traversal. This lets us detect cycles.
        latest_visited = set()

        def visit(task):
            if task in latest_visited:
                # TODO(brownhead): Provide a better error for debugging
                raise RuntimeError("Cyclic dependency in tasks.")

            if task in visited:
                return

            latest_visited.add(task)

            for i in task.get_dependencies():
                visit(self.get_task(i))

            result.append(task)
            visited.add(task)

        entry_points = set(self._queue)
        for i in self._queue:
            entry_points -= set(i.get_dependencies())

        # Iterating through the list rather than the set allows us to keep the ordering
        # well-defined
        for i in self._queue:
            if i in entry_points:
                latest_visited = set()
                visit(i)

        return result

    def enqueue(self, task):
        self._queue.append(task)

    def get_task(self, id):
        for i in self._queue:
            if i.id is id:
                return i

        return None

    def __iter__(self):
        return iter(self._get_topologically_sorted_queue())


global_queue = TaskQueue()
__all__.append("global_queue")  # noqa


@utils.public
def get_task(id):
    return global_queue.get_task(id)
