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

    # HACK(brownhead): This method is too complex. There's a few things I can do to make it not-so.
    #     Such as making the get_depends_on_list function's logic exist elsewhere.
    def _get_topologically_sorted_queue(self):  # noqa
        # Will hold the resulting list
        result = []

        # The tasks added to the list already
        visited = set()

        # Tasks that we've visited in the latest traversal. This lets us detect cycles.
        latest_visited = set()

        def get_depends_on_list(task):
            depends_on_list = []
            if isinstance(task.depends_on, list):
                depends_on_list += task.depends_on
            elif task.depends_on is not None:
                depends_on_list.append(task.depends_on)
            return depends_on_list

        def visit(task):
            if task in latest_visited:
                # TODO(brownhead): Provide a better error for debugging
                raise RuntimeError("Cyclic dependency in tasks.")

            if task in visited:
                return

            latest_visited.add(task)

            for i in get_depends_on_list(task):
                visit(get_task(i))

            result.append(task)
            visited.add(task)

        entry_points = set(self._queue)
        for i in self._queue:
            entry_points -= set(get_depends_on_list(i))

        # Iterating through the list rather than the set allows us to keep the ordering
        # well-defined
        for i in self._queue:
            if i in entry_points:
                latest_visited = set()
                visit(i)

        return result

    def enqueue(self, task):
        self._queue.append(task)

    def __iter__(self):
        return iter(self._get_topologically_sorted_queue())


global_queue = TaskQueue()
__all__.append("global_queue")  # noqa


@utils.public
def get_task(id):
    for i in global_queue._queue:
        if i.id is id:
            return i

    return None
